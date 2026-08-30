from pathlib import Path
from typing import List, Optional
import os
import json
import shutil
import datetime
from fastapi import FastAPI, Request, HTTPException, Header, UploadFile, File, Form, Body, Depends, status
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
from jose import jwt, JWTError
from dotenv import load_dotenv
import resend


# Load Environment Variables
load_dotenv()

# Configuration
VIDEO_DIR = Path("movies")
CONFIG_FILE = Path("config.json")
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for streaming
ADMIN_PASSWORD = "admin"  # Hardcoded default password (legacy)

# Auth & DB Config
MONGODB_URL = os.getenv("MONGODB_URL")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize External Services
if not MONGODB_URL:
    print("⚠ Warning: MONGODB_URL not found in .env")
if not RESEND_API_KEY:
    print("⚠ Warning: RESEND_API_KEY not found in .env")
else:
    resend.api_key = RESEND_API_KEY

# Database Setup
client = AsyncIOMotorClient(MONGODB_URL)
db = client.ott_db
users_collection = db.users

# Security Setup - Direct Bcrypt
# pwd_context removed due to incompatibility

app = FastAPI(title="Video Streaming API")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Models ---
class Video:
    def __init__(self, id: str, title: str, path: Path):
        self.id = id
        self.title = title
        self.path = path

class AdminLoginRequest(BaseModel):
    password: str

class VideoRenameRequest(BaseModel):
    old_id: str
    new_id: str

class PremierConfig(BaseModel):
    video_id: str
    custom_title: Optional[str] = None
    custom_description: Optional[str] = None

class MovieResolveRequest(BaseModel):
    name: str

# Auth Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserInDB(UserRegister):
    hashed_password: str

# --- Helper Functions ---

def verify_password(plain_password, hashed_password):
    # Check if password matches
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    # Generate salt and hash
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def _send_html_email(to_email: str, subject: str, content_html: str):
    """Internal helper to send styled emails."""
    if not RESEND_API_KEY:
        print("Skipping email: Resend API key missing")
        return

    # Netflix-inspired Dark Mode Template
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                background-color: #141414;
                color: #ffffff;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #141414;
            }}
            .header {{
                padding: 20px;
                text-align: center;
                background-color: #000000;
                border-bottom: 1px solid #333;
            }}
            .logo {{
                color: #D4AF37;
                font-size: 32px;
                font-weight: bold;
                text-decoration: none;
                letter-spacing: 2px;
            }}
            .content {{
                padding: 40px 20px;
                text-align: center;
            }}
            .hero-text {{
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 20px;
            }}
            .body-text {{
                font-size: 16px;
                line-height: 1.5;
                color: #cccccc;
                margin-bottom: 30px;
            }}
            .btn {{
                display: inline-block;
                background-color: #D4AF37;
                color: #000000;
                padding: 14px 32px;
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 16px;
            }}
            .footer {{
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #666666;
                border-top: 1px solid #333;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <a href="#" class="logo">AURELION</a>
            </div>
            <div class="content">
                {content_html}
            </div>
            <div class="footer">
                &copy; 2026 Aurelion OTT. All rights reserved.<br>
                Hyderabad, India.
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        r = resend.Emails.send({
            "from": "aurelion@resend.dev",
            "to": to_email,
            "subject": subject,
            "html": html_template
        })
        print(f"Email sent to {to_email}: {r}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_welcome_email(email: str, name: str):
    content = f"""
        <div class="hero-text">Welcome to the Future of Streaming.</div>
        <p class="body-text">
            Hi {name},<br><br>
            Your account has been successfully created. You are now part of the 
            exclusive Aurelion community. Unlimited movies, TV shows, and more 
            are waiting for you.
        </p>
        <a href="http://localhost:3000" class="btn">Start Watching Now</a>
    """
    _send_html_email(email, "Welcome to Aurelion", content)

def send_login_email(email: str):
    content = f"""
        <div class="hero-text">New Login Detected</div>
        <p class="body-text">
            We noticed a new login to your Aurelion account associated with 
            <strong>{email}</strong>.<br><br>
            If this was you, you can safely ignore this email. If you didn't 
            sign in, please reset your password immediately to secure your account.
        </p>
        <a href="http://localhost:3000/account" class="btn" style="background-color: #333;">Manage Account</a>
    """
    _send_html_email(email, "New Login Alert", content)

def get_video_library() -> List[Video]:
    """Scans the VIDEO_DIR and returns a list of available videos."""
    videos = []
    if not VIDEO_DIR.exists():
        VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {VIDEO_DIR.absolute()}")
        print(f"Please add .mp4 files to {VIDEO_DIR.absolute()}")
    
    for file_path in VIDEO_DIR.glob("*.mp4"):
        vid_id = file_path.stem
        videos.append(Video(id=vid_id, title=file_path.stem, path=file_path))
    
    return videos

def get_video_by_id(video_id: str) -> Optional[Video]:
    """Find a video by its ID."""
    library = get_video_library()
    return next((v for v in library if v.id == video_id), None)

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def get_video_duration(file_path: Path) -> int:
    """Get video duration in seconds. Returns 0 if ffprobe not available."""
    try:
        import subprocess
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 
             'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
             str(file_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        return int(float(result.stdout.strip()))
    except (subprocess.SubprocessError, FileNotFoundError, ValueError):
        return 0

def generate_thumbnail(video_path: Path, thumb_path: Path):
    """Generates a thumbnail from the video using ffmpeg."""
    try:
        import subprocess
        # Capture frame at 5 seconds
        subprocess.run(
            ['ffmpeg', '-i', str(video_path), '-ss', '00:00:05.000', '-vframes', '1', str(thumb_path), '-y'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

# --- API Endpoints ---

@app.get("/")
async def root():
    """API health check."""
    return {
        "status": "online",
        "service": "OTT Backend",
        "endpoints": {
            "signup": "/api/auth/signup",
            "login": "/api/auth/login",
            "list_videos": "/api/videos",
            "metadata": "/api/v1/videos/{video_id}/metadata",
            "stream": "/api/v1/videos/{video_id}/stream",
            "admin_login": "/api/admin/login"
        }
    }

# --- Auth Endpoints ---

@app.post("/api/auth/signup", response_model=Token)
async def signup(user: UserRegister):
    # Check if user exists
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    user_dict = user.dict()
    user_dict["hashed_password"] = hashed_password
    del user_dict["password"]
    
    await users_collection.insert_one(user_dict)
    
    # Send email
    send_welcome_email(user.email, user.full_name)
    
    # Generate token
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=Token)
async def login(user: UserLogin):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Send email
    send_login_email(user.email)

    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Admin Endpoints ---

@app.post("/api/admin/login")
async def admin_login(request: AdminLoginRequest):
    if request.password == ADMIN_PASSWORD:
        return {"success": True, "token": "admin-session-valid"}
    raise HTTPException(status_code=401, detail="Invalid password")

@app.get("/api/admin/config")
async def get_admin_config():
    return load_config()

@app.post("/api/admin/rename")
async def rename_video(request: VideoRenameRequest):
    video = get_video_by_id(request.old_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    new_path = video.path.parent / f"{request.new_id}.mp4"
    new_thumb = video.path.parent / f"{request.new_id}.jpg"
    old_thumb = video.path.parent / f"{request.old_id}.jpg"

    if new_path.exists():
        raise HTTPException(status_code=400, detail="Target filename already exists")
        
    try:
        video.path.rename(new_path)
        if old_thumb.exists():
            old_thumb.rename(new_thumb)
        return {"success": True, "new_id": request.new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/premier")
async def set_premier(config: PremierConfig):
    current_config = load_config()
    current_config["premier"] = config.dict()
    save_config(current_config)
    return {"success": True, "config": current_config}

@app.post("/api/admin/upload")
async def upload_video(file: UploadFile = File(...)):
    if not VIDEO_DIR.exists():
        VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        
    file_path = VIDEO_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Attempt to generate thumbnail immediately
    thumb_path = file_path.with_suffix('.jpg')
    generate_thumbnail(file_path, thumb_path)

    return {"success": True, "filename": file.filename, "id": file_path.stem}

# --- Public/User Endpoints ---

@app.get("/api/videos")
async def list_videos(request: Request):
    """Returns a JSON catalog of available videos."""
    library = get_video_library()
    base_url = str(request.base_url).rstrip("/")
    return [
        {
            "id": v.id,
            "title": v.title,
            "thumbnail": f"{base_url}/api/thumbnails/{v.id}"
        }
        for v in library
    ]

@app.get("/api/thumbnails/{video_id}")
async def get_thumbnail(video_id: str):
    """Returns the thumbnail for a video, generating it if needed."""
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    thumb_path = video.path.with_suffix('.jpg')
    
    if not thumb_path.exists():
        generate_thumbnail(video.path, thumb_path)
        
    if thumb_path.exists():
        return FileResponse(thumb_path)
    
    # Fallback if generation failed
    return StreamingResponse(
        content=iter([b"", b""]),
        status_code=307, 
        headers={"Location": f"https://via.placeholder.com/300x169.png?text={video.title.replace(' ', '+')}"}
    )

@app.post("/api/v1/movies/resolve")
async def resolve_movie(request: MovieResolveRequest):
    """Resolves a movie name to a system ID."""
    # Check local library
    library = get_video_library()
    for v in library:
        if v.title.lower() == request.name.lower():
            return {"id": v.id, "found": True}
    
    return {"id": None, "found": False}

@app.get("/api/premier")
async def get_premier():
    """Returns the configured premier movie metadata."""
    config = load_config()
    premier_config = config.get("premier", {})
    
    if not premier_config or not premier_config.get("video_id"):
        return None

    video_id = premier_config["video_id"]
    video = get_video_by_id(video_id)
    
    if video:
        return {
            "id": video.id,
            "title": premier_config.get("custom_title") or video.title,
            "overview": premier_config.get("custom_description") or "Premier Movie",
            "backdrop_path": None,
            "is_local": True
        }
    return None

@app.get("/api/v1/videos/{video_id}/metadata")
async def get_video_metadata(video_id: str):
    video = get_video_by_id(video_id)
    if not video:
        # List available videos to help debug
        library = get_video_library()
        available_ids = [v.id for v in library]
        raise HTTPException(
            status_code=404, 
            detail=f"Video '{video_id}' not found. Available videos: {available_ids}"
        )

    duration = get_video_duration(video.path)
    file_size = video.path.stat().st_size
    
    return {
        "metadata": {
            "title": video.title,
            "quality": "HD",
            "duration": duration,
            "size": file_size
        }
    }

@app.get("/api/v1/videos/{video_id}/stream")
async def stream_video(video_id: str, range: Optional[str] = Header(None)):
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    file_path = video.path
    file_size = file_path.stat().st_size
    start = 0
    end = file_size - 1
    status_code = 200

    if range:
        status_code = 206
        try:
            range_header = range.strip()
            if range_header.startswith("bytes="):
                range_value = range_header[6:]
                range_parts = range_value.split("-")
                start = int(range_parts[0]) if range_parts[0] else 0
                end = int(range_parts[1]) if len(range_parts) > 1 and range_parts[1] else file_size - 1
                start = max(0, min(start, file_size - 1))
                end = min(file_size - 1, end)
        except ValueError:
            pass

    content_length = (end - start) + 1
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": "video/mp4",
        "Cache-Control": "public, max-age=3600",
    }
    
    if status_code == 206:
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"

    def file_iterator(file_path, offset, length):
        with open(file_path, "rb") as f:
            f.seek(offset)
            bytes_read = 0
            while bytes_read < length:
                chunk_size = min(CHUNK_SIZE, length - bytes_read)
                data = f.read(chunk_size)
                if not data: break
                bytes_read += len(data)
                yield data

    return StreamingResponse(
        file_iterator(file_path, start, content_length),
        status_code=status_code,
        headers=headers,
        media_type="video/mp4"
    )

# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("=" * 60)
    print("Video Streaming API Started")
    print("=" * 60)
    videos = get_video_library()
    if videos:
        print(f"Found {len(videos)} video(s): {[v.title for v in videos]}")
    else:
        print(f"No videos found in {VIDEO_DIR.absolute()}")
    print("\nServer ready at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("=" * 60)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")