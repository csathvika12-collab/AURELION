import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def clean_db():
    load_dotenv()
    mongo_url = os.getenv("MONGODB_URL")
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client.ott_db
        collection = db.users
        
        # Delete specific test users
        result = await collection.delete_many({
            "email": {"$in": ["test_script_user@example.com", "api_test_user@example.com"]}
        })
        
        print(f"✓ Removed {result.deleted_count} test user(s).")
        
        # Verify
        count = await collection.count_documents({})
        print(f"Current user count: {count}")
        
    except Exception as e:
        print(f"❌ Failed to clean DB: {e}")

if __name__ == "__main__":
    asyncio.run(clean_db())
