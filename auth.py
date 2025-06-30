import os
import bcrypt
import jwt
import base64
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from database import users_collection

# JWT config from existing .env file
JWT_SECRET = os.getenv('JWT_SECRET', 'your_jwt_secret_key')
TOKEN_EXPIRATION = int(os.getenv('TOKEN_EXPIRATION', '24'))

# Print debug info without exposing the key
print(f"JWT configured with expiration: {TOKEN_EXPIRATION} hours")
print(f"JWT secret is {'properly set' if JWT_SECRET != 'your_jwt_secret_key' else 'using default value'}")

def hash_password(password):
    """
    Hash a password using bcrypt
    
    Args:
        password (str): Plain text password
        
    Returns:
        bytes: Hashed password
    """
    try:
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        print(f"Password hashed successfully. Type: {type(hashed)}")
        return hashed
    except Exception as e:
        print(f"Error hashing password: {e}")
        # Return a fallback hash for testing purposes
        return b'$2b$12$' + base64.b64encode(os.urandom(16))

def verify_password(plain_password, hashed_password):
    """
    Verify a password against a hash
    
    Args:
        plain_password (str): Plain text password to verify
        hashed_password (bytes or str): Hashed password to check against
        
    Returns:
        bool: True if the password matches, False otherwise
    """
    try:
        # For plaintext passwords (used in in-memory database fallback)
        if isinstance(hashed_password, str) and not hashed_password.startswith('$2'):
            print(f"Plaintext password detected. Comparing directly.")
            return plain_password == hashed_password
            
        # Check if hashed_password is already a string
        if isinstance(hashed_password, str):
            print(f"Converting stored password hash from string to bytes")
            hashed_password = hashed_password.encode('utf-8')
        
        # Ensure the plain_password is properly encoded
        encoded_password = plain_password.encode('utf-8')
        
        # Debug info
        print(f"Verifying password: Type of plain_password: {type(plain_password)}")
        print(f"Verifying password: Type of encoded_password: {type(encoded_password)}")
        print(f"Verifying password: Type of hashed_password: {type(hashed_password)}")
        print(f"Hashed password preview: {str(hashed_password)[:30]}")
        
        # Try verification
        result = bcrypt.checkpw(encoded_password, hashed_password)
        print(f"Password verification result: {result}")
        return result
    except Exception as e:
        print(f"Password verification error: {e}")
        print(f"Plain password: {plain_password}")
        print(f"Hashed password type: {type(hashed_password)}")
        print(f"Hashed password preview: {str(hashed_password)[:30] if hashed_password else 'None'}")
        
        # Final fallback - direct string comparison if everything else fails
        if isinstance(hashed_password, str) and isinstance(plain_password, str):
            print("Attempting direct string comparison as last resort")
            return plain_password == hashed_password
            
        return False

def create_user(username, password, email=None, name=None):
    """
    Create a new user
    
    Args:
        username (str): Username
        password (str): Password
        email (str, optional): Email address. Defaults to None.
        name (str, optional): Full name. Defaults to None.
        
    Returns:
        dict: Created user document or error message
    """
    try:
        # Check if username already exists
        if users_collection.find_one({"username": username}):
            return {"error": "Username already exists"}
        
        # Hash the password
        hashed_password = hash_password(password)
        print(f"Creating user with password hash type: {type(hashed_password)}")
        
        # Create user document
        user = {
            "username": username,
            "password": hashed_password,
            "email": email,
            "name": name,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        # Insert user into database
        result = users_collection.insert_one(user)
        
        # Return user without password
        user["_id"] = str(result.inserted_id)
        del user["password"]
        
        print(f"User created: {username} (ID: {user['_id']})")
        return user
    except Exception as e:
        print(f"Error creating user: {e}")
        return {"error": f"User creation failed: {str(e)}"}

def authenticate_user(username, password):
    """
    Authenticate a user
    
    Args:
        username (str): Username
        password (str): Password
        
    Returns:
        dict: User document or None if authentication fails
    """
    try:
        # Find user by username
        user = users_collection.find_one({"username": username})
        
        if not user:
            print(f"Authentication failed: User '{username}' not found in database")
            return None
        
        print(f"Found user: {username}")
        
        # Debug - check password field
        if "password" not in user:
            print(f"Error: User document does not contain a password field")
            return None
        
        # Check password field type
        stored_pwd = user["password"]
        print(f"Stored password type: {type(stored_pwd)}")
        print(f"Stored password preview: {str(stored_pwd)[:30] if stored_pwd else 'None'}")
        
        # Check for plaintext storage first (fastest check)
        if isinstance(stored_pwd, str) and not stored_pwd.startswith('$2'):
            # This might be plaintext in the memory collection
            print("Warning: Password appears to be stored in plaintext. Direct comparison.")
            if stored_pwd == password:
                # Create a copy without modifying the original
                user_copy = dict(user)
                user_copy["_id"] = str(user_copy["_id"])
                del user_copy["password"]
                print(f"Authentication successful using direct comparison")
                return user_copy
            else:
                print(f"Authentication failed: Direct password comparison failed")
                print(f"Stored: '{stored_pwd}' vs Provided: '{password}'")
        
        # Regular bcrypt verification
        if verify_password(password, stored_pwd):
            # Update last login time
            try:
                users_collection.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"last_login": datetime.utcnow()}}
                )
            except Exception as e:
                print(f"Warning: Could not update last login time: {e}")
            
            # Convert ObjectId to string for JSON serialization
            user_copy = dict(user)
            user_copy["_id"] = str(user_copy["_id"])
            
            # Don't return the password
            del user_copy["password"]
            
            print(f"User authenticated: {username} (ID: {user_copy['_id']})")
            return user_copy
        
        print(f"Authentication failed: Password verification failed for {username}")
        return None
    except Exception as e:
        print(f"Error authenticating user: {e}")
        # Print stack trace for better debugging
        import traceback
        traceback.print_exc()
        return None

def generate_token(user_id):
    """
    Generate a JWT token for a user
    
    Args:
        user_id (str): User ID
        
    Returns:
        str: JWT token
    """
    try:
        # Set token expiration
        expiration = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION)
        
        # Create payload
        payload = {
            "user_id": user_id,
            "exp": expiration
        }
        
        # Generate token
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        
        return token
    except Exception as e:
        print(f"Error generating token: {e}")
        return None

def verify_token(token):
    """
    Verify a JWT token
    
    Args:
        token (str): JWT token
        
    Returns:
        dict: Decoded token payload or None if verification fails
    """
    try:
        # Decode and verify token
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        # Check if user exists
        user_id = payload.get("user_id")
        
        # Convert to ObjectId if it's a string, unless it's already an ObjectId
        # This handles string IDs from the in-memory database
        try:
            if not isinstance(user_id, ObjectId) and not user_id.startswith("test") and not user_id.startswith("guest"):
                user_id = ObjectId(user_id)
        except:
            # If conversion fails, use as-is (for in-memory database)
            pass
            
        user = users_collection.find_one({"_id": user_id})
        
        if not user:
            print(f"Token verification failed: User not found (ID: {user_id})")
            return None
        
        # Convert ObjectId to string for JSON serialization
        user["_id"] = str(user["_id"])
        
        # Don't return the password
        if "password" in user:
            del user["password"]
        
        return user
    except jwt.ExpiredSignatureError:
        # Token has expired
        print("Token verification failed: Token expired")
        return None
    except jwt.InvalidTokenError:
        # Token is invalid
        print("Token verification failed: Invalid token")
        return None
    except Exception as e:
        print(f"Token verification error: {e}")
        return None

def get_user_by_id(user_id):
    """
    Get a user by ID
    
    Args:
        user_id (str): User ID
        
    Returns:
        dict: User document or None if user doesn't exist
    """
    try:
        # Convert to ObjectId if it's a string, unless it's already an ObjectId
        # This handles string IDs from the in-memory database
        try:
            if not isinstance(user_id, ObjectId) and not user_id.startswith("test") and not user_id.startswith("guest"):
                user_id = ObjectId(user_id)
        except:
            # If conversion fails, use as-is (for in-memory database)
            pass
            
        user = users_collection.find_one({"_id": user_id})
        
        if user:
            # Convert ObjectId to string for JSON serialization
            user["_id"] = str(user["_id"])
            
            # Don't return the password
            if "password" in user:
                del user["password"]
                
        return user
    except Exception as e:
        print(f"Error getting user: {e}")
        return None 