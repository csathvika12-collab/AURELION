import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def check_user():
    load_dotenv()
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client.ott_db
    user = await db.users.find_one({"email": "csathvika10@gmail.com"})
    if user:
        print("User 'csathvika10@gmail.com' EXISTS in MongoDB.")
    else:
        print("User 'csathvika10@gmail.com' does NOT exist in MongoDB.")

if __name__ == "__main__":
    asyncio.run(check_user())
