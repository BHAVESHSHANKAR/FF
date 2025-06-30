from auth import authenticate_user, generate_token

def test_guest_login():
    """Test logging in with the guest account"""
    print("\n=== Testing Guest Login ===\n")
    
    # Guest credentials (from in-memory database)
    username = "guest"
    password = "style123"
    
    print(f"Attempting to login with:\nUsername: {username}\nPassword: {password}")
    
    # Authenticate user
    user = authenticate_user(username, password)
    
    if user is None:
        print("❌ Guest authentication failed")
        return
    
    print(f"✅ Guest authentication succeeded!")
    print(f"User details: {user}")
    
    # Generate token
    token = generate_token(user["_id"])
    
    if token is None:
        print("❌ Token generation failed")
        return
    
    print(f"✅ Token generated: {token[:20]}...")
    print("\n=== Guest Login Test Complete ===\n")

if __name__ == "__main__":
    test_guest_login()