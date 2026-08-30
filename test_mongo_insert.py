import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def test_mongo_insert():
    load_dotenv()
    mongo_url = os.getenv("MONGODB_URL")
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client.ott_db
        collection = db.users
        
        # Test Data
        test_user = {
            "email": "test_script_user@example.com",
            "full_name": "Test Script User",
            "hashed_password": "fakehashedpassword"
        }
        
        # Check if exists
        existing = await collection.find_one({"email": test_user["email"]})
        if existing:
            print("Test user already exists. Deleting...")
            await collection.delete_one({"email": test_user["email"]})
            
        print("Attempting to insert test user...")
        result = await collection.insert_one(test_user)
        print(f"✓ Inserted user with ID: {result.inserted_id}")
        
        # Verify
        count = await collection.count_documents({})
        print(f"Total users count: {count}")
        
    except Exception as e:
        print(f"❌ Database operation failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_mongo_insert())
