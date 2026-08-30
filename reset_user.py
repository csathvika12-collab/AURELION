import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def reset_user():
    load_dotenv()
    mongo_url = os.getenv("MONGODB_URL")
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client.ott_db
        collection = db.users
        
        email_to_reset = "csathvika10@gmail.com"
        
        result = await collection.delete_one({"email": email_to_reset})
        
        if result.deleted_count > 0:
            print(f"✓ Success: User '{email_to_reset}' has been removed.")
            print("You can now Sign Up again with this email to see the new email design!")
        else:
            print(f"ℹ User '{email_to_reset}' was not found in the database.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(reset_user())
