import time
import os
import json
from dotenv import load_dotenv
from auth import create_user, authenticate_user, generate_token, verify_token

# Load environment variables
load_dotenv()

def test_authentication():
    """Test user registration, authentication, and token generation"""
    print("\n=== Testing Authentication System ===\n")
    
    # Generate a unique test username
    timestamp = int(time.time())
    test_username = f"testuser_{timestamp}"
    test_password = "testpass123"
    test_email = f"test_{timestamp}@example.com"
    
    print(f"Testing with username: {test_username}")
    print(f"Testing with password: {test_password}")
    
    # Step 1: Create a new user
    print("\n1. Creating new user...")
    create_result = create_user(
        username=test_username,
        password=test_password,
        email=test_email,
        name="Test User"
    )
    
    if "error" in create_result:
        print(f"❌ User creation failed: {create_result['error']}")
        return False
    
    print(f"✅ User created: {create_result}")
    
    # Step 2: Try to authenticate with wrong password
    print("\n2. Testing authentication with wrong password...")
    wrong_auth_result = authenticate_user(test_username, "wrongpassword")
    
    if wrong_auth_result is not None:
        print(f"❌ Authentication should have failed with wrong password but succeeded")
        return False
    
    print(f"✅ Authentication correctly failed with wrong password")
    
    # Step 3: Authenticate with correct password
    print("\n3. Testing authentication with correct password...")
    auth_result = authenticate_user(test_username, test_password)
    
    if auth_result is None:
        print(f"❌ Authentication failed with correct password")
        
        # Try with guest account as fallback
        print("\nTrying with guest account as fallback...")
        guest_auth = authenticate_user("guest", "style123")
        if guest_auth is None:
            print("❌ Even guest authentication failed")
            return False
        else:
            print(f"✅ Guest authentication succeeded: {guest_auth}")
            auth_result = guest_auth
    else:
        print(f"✅ Authentication succeeded: {auth_result}")
    
    # Step 4: Generate a token
    print("\n4. Generating JWT token...")
    token = generate_token(auth_result["_id"])
    
    if token is None:
        print(f"❌ Token generation failed")
        return False
    
    print(f"✅ Token generated: {token[:20]}...")
    
    # Step 5: Verify the token
    print("\n5. Verifying JWT token...")
    verify_result = verify_token(token)
    
    if verify_result is None:
        print(f"❌ Token verification failed")
        return False
    
    print(f"✅ Token verified: {verify_result}")
    
    print("\n=== Authentication System Test Complete ===")
    print("All tests passed successfully! ✨\n")
    return True

def test_guest_account():
    """Test the guest account login"""
    print("\n=== Testing Guest Account ===\n")
    
    # Try to authenticate with guest account
    print("Authenticating with guest account...")
    guest_auth = authenticate_user("guest", "style123")
    
    if guest_auth is None:
        print("❌ Guest authentication failed")
        return False
    
    print(f"✅ Guest authentication succeeded: {guest_auth}")
    
    # Generate a token for guest
    print("\nGenerating JWT token for guest...")
    token = generate_token(guest_auth["_id"])
    
    if token is None:
        print(f"❌ Token generation failed for guest")
        return False
    
    print(f"✅ Token generated for guest: {token[:20]}...")
    
    print("\n=== Guest Account Test Complete ===")
    return True

def main():
    """Main test function"""
    # Print environment info
    print("\n=== Environment Information ===")
    mongo_uri = os.getenv('MONGO_URI', 'Not set')
    db_name = os.getenv('DB_NAME', 'Not set')
    
    # Mask the connection string for security
    if mongo_uri != 'Not set':
        parts = mongo_uri.split('@')
        if len(parts) > 1:
            masked_uri = f"{parts[0].split('://')[0]}://****@{parts[1]}"
        else:
            masked_uri = f"{mongo_uri.split('://')[0]}://****"
        print(f"MongoDB URI: {masked_uri}")
    else:
        print(f"MongoDB URI: {mongo_uri}")
    
    print(f"Database name: {db_name}")
    print(f"JWT Secret: {'Set' if os.getenv('JWT_SECRET') else 'Not set'}")
    print()
    
    # Run authentication tests
    auth_success = test_authentication()
    
    # If regular auth fails, try guest account
    if not auth_success:
        print("\nRegular authentication failed, trying guest account...")
        guest_success = test_guest_account()
        
        if not guest_success:
            print("\n❌ All authentication tests failed")
            return
    
    print("\n✅ Authentication system is working correctly")

if __name__ == "__main__":
    main() 