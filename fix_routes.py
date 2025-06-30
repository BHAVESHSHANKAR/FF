"""
Route diagnostics script for the Fashion Recommendation API
This script creates a minimal Flask app with the same routes as the main app
to verify if the authentication routes are working correctly.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import jwt
from datetime import datetime, timedelta

# Create a minimal Flask app for testing
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "DELETE"], "allow_headers": ["Content-Type", "Authorization"]}})

# Mock database for testing
users_db = {}

# JWT secret key
JWT_SECRET = "test_jwt_secret"

@app.route('/')
def index():
    """Root endpoint for testing"""
    return jsonify({
        "status": "success",
        "message": "Fashion Recommendation API is running",
        "routes": [
            "/",
            "/test",
            "/api/auth/register",
            "/api/auth/login",
            "/api/auth/me"
        ]
    })

@app.route('/test')
def test():
    """Test endpoint"""
    return jsonify({
        "status": "success",
        "message": "Test endpoint is working"
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    Test register endpoint
    Expected JSON body: {"username": "...", "password": "...", "email": "...", "name": "..."}
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Check required fields
    if not data.get("username") or not data.get("password"):
        return jsonify({"error": "Username and password are required"}), 400
    
    # Check if user already exists
    if data["username"] in users_db:
        return jsonify({"error": "Username already exists"}), 400
    
    # Create user (just store in memory for this test)
    user = {
        "_id": str(len(users_db) + 1),
        "username": data["username"],
        "email": data.get("email"),
        "name": data.get("name"),
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Store password separately (simulating hashing)
    users_db[data["username"]] = {
        "user": user,
        "password": data["password"]
    }
    
    # Generate token
    payload = {
        "user_id": user["_id"],
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    return jsonify({
        "user": user,
        "token": token
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Test login endpoint
    Expected JSON body: {"username": "...", "password": "..."}
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Check required fields
    if not data.get("username") or not data.get("password"):
        return jsonify({"error": "Username and password are required"}), 400
    
    # Check if user exists and password matches
    if data["username"] not in users_db or users_db[data["username"]]["password"] != data["password"]:
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Get user data
    user = users_db[data["username"]]["user"]
    
    # Generate token
    payload = {
        "user_id": user["_id"],
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    return jsonify({
        "user": user,
        "token": token
    })

@app.route('/api/auth/me', methods=['GET'])
def get_me():
    """
    Test get current user endpoint
    Requires Authorization header with Bearer token
    """
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return jsonify({"error": "Authentication required"}), 401
    
    # Check if header is in the correct format: "Bearer <token>"
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return jsonify({"error": "Invalid authorization format"}), 401
    
    token = parts[1]
    
    try:
        # Decode token
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        # Find user by ID
        user_id = payload.get("user_id")
        
        # Look through users to find matching ID
        user = None
        for username, data in users_db.items():
            if data["user"]["_id"] == user_id:
                user = data["user"]
                break
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify(user)
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

if __name__ == "__main__":
    print("Starting minimal Flask app to test authentication routes...")
    print("Available endpoints:")
    print("  GET  /")
    print("  GET  /test")
    print("  POST /api/auth/register")
    print("  POST /api/auth/login")
    print("  GET  /api/auth/me")
    print("\nTest with: python test_integration.py")
    
    # Add test user for convenience
    test_user = {
        "_id": "1",
        "username": "test_user",
        "email": "test@example.com",
        "name": "Test User",
        "created_at": datetime.utcnow().isoformat()
    }
    users_db["test_user"] = {
        "user": test_user,
        "password": "password123"
    }
    
    # Run the app
    app.run(debug=True, port=5000) 