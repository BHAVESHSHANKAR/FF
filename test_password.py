import bcrypt
from database import users_collection

def test_password_verification():
    """Test different methods of password verification to debug login issues"""
    print("\n=== Testing Password Verification Methods ===\n")
    
    # Test data
    username = "guest"
    password = "style123"
    
    # Get user from database
    user = users_collection.find_one({"username": username})
    
    if not user:
        print(f"❌ User '{username}' not found in database")
        return
    
    print(f"✅ Found user: {username}")
    
    # Check password field
    if "password" not in user:
        print(f"❌ User document does not contain a password field")
        return
    
    # Get stored password
    stored_password = user["password"]
    print(f"Stored password type: {type(stored_password)}")
    
    # If it's a string, print it
    if isinstance(stored_password, str):
        print(f"Stored password (string): {stored_password[:30]}...")
        
        # Try direct comparison if it doesn't look like a bcrypt hash
        if not stored_password.startswith('$2'):
            print("\nTesting direct string comparison:")
            if stored_password == password:
                print("✅ Direct string comparison succeeded")
            else:
                print(f"❌ Direct string comparison failed")
                print(f"Stored: '{stored_password}' vs Provided: '{password}'")
        
        # Try to convert to bytes and use bcrypt
        try:
            print("\nTesting bcrypt comparison with string->bytes conversion:")
            stored_bytes = stored_password.encode('utf-8')
            plain_bytes = password.encode('utf-8')
            
            if bcrypt.checkpw(plain_bytes, stored_bytes):
                print("✅ bcrypt comparison succeeded after string->bytes conversion")
            else:
                print("❌ bcrypt comparison failed after string->bytes conversion")
        except Exception as e:
            print(f"❌ Error in bcrypt comparison after conversion: {e}")
    
    # If it's bytes, use bcrypt directly
    elif isinstance(stored_password, bytes):
        print(f"Stored password (bytes): {stored_password[:30]}...")
        
        try:
            print("\nTesting bcrypt comparison with bytes:")
            plain_bytes = password.encode('utf-8')
            
            if bcrypt.checkpw(plain_bytes, stored_password):
                print("✅ bcrypt comparison succeeded with bytes")
            else:
                print("❌ bcrypt comparison failed with bytes")
        except Exception as e:
            print(f"❌ Error in bcrypt comparison with bytes: {e}")
    
    # Create a new hash from the password for comparison
    try:
        print("\nGenerate new hash from password:")
        new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        print(f"New hash type: {type(new_hash)}")
        print(f"New hash: {new_hash[:30]}...")
        
        # Verify the new hash
        if bcrypt.checkpw(password.encode('utf-8'), new_hash):
            print("✅ Verification with new hash succeeded")
        else:
            print("❌ Verification with new hash failed")
    except Exception as e:
        print(f"❌ Error generating or verifying new hash: {e}")
    
    print("\n=== Password Verification Test Complete ===\n")

if __name__ == "__main__":
    test_password_verification() 