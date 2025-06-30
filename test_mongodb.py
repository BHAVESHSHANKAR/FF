import os
import time
from database import db, MONGO_URI
from auth import create_user, authenticate_user, generate_token, verify_token
from datetime import datetime

def test_mongodb_connection():
    """Test MongoDB connection and basic operations"""
    print("=== Testing MongoDB Connection ===")
    
    try:
        # Test the users collection
        users = db['users']
        
        # Count current users
        existing_count = len(list(users.find({})))
        print(f"Current user count: {existing_count}")
        
        # Create a test user with timestamp to ensure uniqueness
        timestamp = int(time.time())
        test_username = f"testuser_{timestamp}"
        test_password = "testpassword123"
        
        print(f"Creating test user: {test_username}")
        
        # Create the user
        user = create_user(
            username=test_username,
            password=test_password,
            email=f"{test_username}@example.com",
            name="Test User"
        )
        
        if "error" in user:
            print(f"Error creating user: {user['error']}")
            return False
        
        print(f"User created successfully with ID: {user['_id']}")
        
        # Test authentication
        print(f"Authenticating user: {test_username}")
        auth_user = authenticate_user(test_username, test_password)
        
        if not auth_user:
            print("Authentication failed!")
            return False
        
        print("Authentication successful!")
        
        # Test token generation and verification
        print("Generating JWT token")
        token = generate_token(auth_user["_id"])
        
        print(f"Token: {token[:10]}...{token[-10:]}")
        
        print("Verifying token")
        verified_user = verify_token(token)
        
        if not verified_user:
            print("Token verification failed!")
            return False
        
        print("Token verified successfully!")
        print(f"Verified user ID: {verified_user['_id']}")
        
        return True
    
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    print(f"MongoDB URI: {MONGO_URI.split('@')[0].split('://')[0]}://*****@{MONGO_URI.split('@')[1] if '@' in MONGO_URI else 'localhost'}")
    
    success = test_mongodb_connection()
    
    if success:
        print("\n✅ MongoDB connection and authentication tests passed!")
    else:
        print("\n❌ MongoDB tests failed!") 