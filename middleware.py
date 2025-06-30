from functools import wraps
from flask import request, jsonify
from auth import verify_token
import traceback

def auth_required(f):
    """
    Decorator to require authentication for a route
    
    Args:
        f: The route function to protect
        
    Returns:
        Function: Wrapped function that checks for authentication
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                print("Authentication failed: No Authorization header")
                return jsonify({"error": "Authentication required"}), 401
            
            # Check if header is in the correct format: "Bearer <token>"
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                print(f"Authentication failed: Invalid authorization format: {auth_header[:15]}...")
                return jsonify({"error": "Invalid authorization format", "detail": "Use format 'Bearer <token>'"}), 401
            
            token = parts[1]
            
            # Verify token
            user = verify_token(token)
            
            if not user:
                print("Authentication failed: Invalid or expired token")
                return jsonify({"error": "Invalid or expired token"}), 401
            
            # Add user to request object
            request.user = user
            
            # Log successful authentication
            print(f"Authentication successful for user: {user.get('username', user.get('_id', 'unknown'))}")
            
            # Continue to the route function
            return f(*args, **kwargs)
        
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            print(traceback.format_exc())
            return jsonify({"error": "Authentication failed", "detail": str(e)}), 500
    
    return decorated 