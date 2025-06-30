import bcrypt
import os
import time
from dotenv import load_dotenv
from database import users_collection

def create_test_user():
    """
    Create a test user with a known password directly in the database
    """
    print("\n=== Creating Test User ===\n")
    
    # Define test user
    username = "testuser"
    password = "testpass123"
    
    # Check if user already exists
    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        print(f"User '{username}' already exists in the database")
        print(f"Password type: {type(existing_user.get('password'))}")
        print(f"Password preview: {str(existing_user.get('password'))[:30]}")
        return
    
    # Create password hash
    print(f"Creating user with username: {username}, password: {password}")
    
    try:
        # Hash the password
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        
        print(f"Generated password hash type: {type(hashed_password)}")
        print(f"Generated password hash: {hashed_password[:30]}")
        
        # Create user document
        user = {
            "username": username,
            "password": hashed_password,
            "email": f"{username}@example.com",
            "name": "Test User",
            "created_at": time.time(),
            "last_login": None
        }
        
        # Insert into database
        result = users_collection.insert_one(user)
        
        print(f"✅ User created successfully with ID: {result.inserted_id}")
        
        # Test retrieving the user
        created_user = users_collection.find_one({"username": username})
        if created_user:
            print(f"✅ User retrieved from database")
            print(f"Password type: {type(created_user.get('password'))}")
            print(f"Password preview: {str(created_user.get('password'))[:30]}")
        else:
            print(f"❌ User could not be retrieved from database")
            
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        
        # Try with plaintext as a fallback
        print("Trying with plaintext password as fallback...")
        
        try:
            # Create user document with plaintext password
            user = {
                "username": username,
                "password": password,  # Plaintext
                "email": f"{username}@example.com",
                "name": "Test User",
                "created_at": time.time(),
                "last_login": None
            }
            
            # Insert into database
            result = users_collection.insert_one(user)
            
            print(f"✅ User created with plaintext password, ID: {result.inserted_id}")
        except Exception as e2:
            print(f"❌ Even plaintext fallback failed: {e2}")
    
    print("\n=== Test User Creation Complete ===\n")
    
if __name__ == "__main__":
    load_dotenv()
    create_test_user() 