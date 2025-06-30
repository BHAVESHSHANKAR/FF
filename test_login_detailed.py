import bcrypt
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from auth import authenticate_user, create_user, generate_token, verify_token
from database import users_collection

# Load environment variables
load_dotenv()

def log_separator():
    """Print a log separator for better readability"""
    print("\n" + "="*80 + "\n")

def print_json(data):
    """Print data as formatted JSON"""
    print(json.dumps(data, indent=2, default=str))

def test_create_and_login():
    """Test creating a user and then logging in"""
    log_separator()
    print("TEST: CREATE USER AND LOGIN")
    log_separator()
    
    # Create a unique username
    timestamp = int(time.time())
    username = f"testuser_{timestamp}"
    password = "testpass123"
    email = f"test_{timestamp}@example.com"
    
    print(f"Creating user: {username}")
    print(f"Password: {password}")
    
    # Create the user
    user = create_user(username, password, email)
    
    # Check if user creation was successful
    if "error" in user:
        print(f"❌ User creation failed: {user['error']}")
        return False
    
    print(f"✅ User created successfully:")
    print_json(user)
    
    # Now try to login
    print("\nTesting login with created user")
    auth_user = authenticate_user(username, password)
    
    if not auth_user:
        print(f"❌ Login failed for user {username}")
        return False
    
    print(f"✅ Login successful:")
    print_json(auth_user)
    
    # Generate token
    token = generate_token(auth_user["_id"])
    
    if not token:
        print(f"❌ Token generation failed")
        return False
    
    print(f"✅ Token generated: {token[:20]}...")
    
    # Verify token
    verified_user = verify_token(token)
    
    if not verified_user:
        print(f"❌ Token verification failed")
        return False
    
    print(f"✅ Token verified successfully:")
    print_json(verified_user)
    
    return True

def test_direct_mongodb():
    """Test direct interaction with MongoDB"""
    log_separator()
    print("TEST: DIRECT MONGODB INTERACTION")
    log_separator()
    
    # Create a unique username
    timestamp = int(time.time())
    username = f"dbtest_{timestamp}"
    password = "dbpass123"
    
    print(f"Creating user directly in MongoDB: {username}")
    
    try:
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user document
        user = {
            "username": username,
            "password": hashed_password,
            "email": f"{username}@example.com",
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        # Insert user
        result = users_collection.insert_one(user)
        user_id = result.inserted_id
        
        print(f"✅ User inserted with ID: {user_id}")
        
        # Retrieve the user
        db_user = users_collection.find_one({"_id": user_id})
        
        if not db_user:
            print(f"❌ Failed to retrieve user from database")
            return False
        
        print(f"✅ User retrieved from database:")
        print(f"  Username: {db_user.get('username')}")
        print(f"  Password type: {type(db_user.get('password'))}")
        print(f"  Password: {str(db_user.get('password'))[:30]}...")
        
        # Now try to authenticate
        auth_user = authenticate_user(username, password)
        
        if not auth_user:
            print(f"❌ Authentication failed")
            print("Trying with plaintext password as a test...")
            
            # Update to plaintext for testing
            users_collection.update_one(
                {"_id": user_id},
                {"$set": {"password": password}}
            )
            
            # Try again
            auth_user = authenticate_user(username, password)
            
            if not auth_user:
                print(f"❌ Authentication still failed with plaintext password")
                return False
            else:
                print(f"✅ Authentication succeeded with plaintext password")
        else:
            print(f"✅ Authentication succeeded with hashed password")
        
        print_json(auth_user)
        return True
        
    except Exception as e:
        print(f"❌ Error in direct MongoDB test: {e}")
        return False

def test_guest_account():
    """Test the built-in guest account"""
    log_separator()
    print("TEST: GUEST ACCOUNT")
    log_separator()
    
    username = "guest"
    password = "style123"
    
    print(f"Testing login with guest account: {username}")
    
    # Try to login
    auth_user = authenticate_user(username, password)
    
    if not auth_user:
        print(f"❌ Guest login failed")
        return False
    
    print(f"✅ Guest login successful:")
    print_json(auth_user)
    
    # Generate token
    token = generate_token(auth_user["_id"])
    
    if not token:
        print(f"❌ Token generation failed for guest")
        return False
    
    print(f"✅ Token generated for guest: {token[:20]}...")
    
    return True

def debug_password_verification(username, password):
    """Debug password verification for a specific user"""
    log_separator()
    print(f"DEBUGGING PASSWORD VERIFICATION FOR: {username}")
    log_separator()
    
    # Retrieve user from database
    user = users_collection.find_one({"username": username})
    
    if not user:
        print(f"❌ User not found in database: {username}")
        return False
    
    print(f"✅ User found in database:")
    print(f"  ID: {user.get('_id')}")
    print(f"  Email: {user.get('email')}")
    
    # Check password
    if "password" not in user:
        print(f"❌ User does not have a password field")
        return False
    
    stored_password = user["password"]
    print(f"  Password type: {type(stored_password)}")
    
    if isinstance(stored_password, bytes):
        print(f"  Password (bytes): {stored_password[:30]}...")
        
        # Test bcrypt verification
        try:
            password_bytes = password.encode('utf-8')
            result = bcrypt.checkpw(password_bytes, stored_password)
            print(f"  bcrypt verification result: {result}")
        except Exception as e:
            print(f"  ❌ Error in bcrypt verification: {e}")
    
    elif isinstance(stored_password, str):
        print(f"  Password (string): {stored_password[:30]}...")
        
        # Test direct comparison
        if stored_password == password:
            print(f"  ✅ Direct string comparison succeeded")
        else:
            print(f"  ❌ Direct string comparison failed")
            
        # If it looks like a bcrypt hash
        if stored_password.startswith('$2'):
            try:
                password_bytes = password.encode('utf-8')
                hash_bytes = stored_password.encode('utf-8')
                result = bcrypt.checkpw(password_bytes, hash_bytes)
                print(f"  bcrypt verification result: {result}")
            except Exception as e:
                print(f"  ❌ Error in bcrypt verification: {e}")
    
    # Try authentication
    auth_user = authenticate_user(username, password)
    
    if not auth_user:
        print(f"❌ Authentication failed for {username}")
    else:
        print(f"✅ Authentication succeeded for {username}")
        print_json(auth_user)
    
    return auth_user is not None

def main():
    """Run all tests"""
    print("\n" + "="*30 + " AUTHENTICATION TESTS " + "="*30 + "\n")
    
    # Print environment information
    print("ENVIRONMENT INFORMATION:")
    mongo_uri = os.getenv('MONGO_URI', 'Not set')
    db_name = os.getenv('DB_NAME', 'Not set')
    jwt_secret = os.getenv('JWT_SECRET', 'Not set')
    
    # Mask the MongoDB URI for security
    if mongo_uri != 'Not set' and '@' in mongo_uri:
        masked_uri = f"{mongo_uri.split('://')[0]}://*****@{mongo_uri.split('@')[1]}"
    else:
        masked_uri = mongo_uri
    
    print(f"MongoDB URI: {masked_uri}")
    print(f"Database name: {db_name}")
    print(f"JWT Secret: {'Set correctly' if jwt_secret != 'Not set' else 'Not set'}")
    
    # Debug password verification for guest account
    debug_password_verification("guest", "style123")
    
    # Run tests
    results = {
        "guest_account": test_guest_account(),
        "create_and_login": test_create_and_login(),
        "direct_mongodb": test_direct_mongodb()
    }
    
    # Print summary
    log_separator()
    print("TEST RESULTS SUMMARY:")
    print(f"Guest account login: {'✅ PASSED' if results['guest_account'] else '❌ FAILED'}")
    print(f"Create user and login: {'✅ PASSED' if results['create_and_login'] else '❌ FAILED'}")
    print(f"Direct MongoDB interaction: {'✅ PASSED' if results['direct_mongodb'] else '❌ FAILED'}")
    
    # Overall status
    if all(results.values()):
        print("\n✅ ALL TESTS PASSED")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    log_separator()

if __name__ == "__main__":
    main() 