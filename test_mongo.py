import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def test_mongo():
    load_dotenv()
    mongo_url = os.getenv("MONGODB_URL")
    print(f"Testing connection to: {mongo_url}")
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        # Force a connection to verify
        await client.admin.command('ping')
        print("✓ Connected successfully to MongoDB!")
        
        db = client.ott_db
        collection = db.users
        
        count = await collection.count_documents({})
        print(f"Current user count in 'ott_db.users': {count}")
        
        users = await collection.find({}).to_list(length=10)
        print("Users found:")
        for user in users:
            print(f" - {user.get('email')}")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_mongo())
