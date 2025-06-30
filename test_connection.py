"""
Connection test utility for Fashion Recommendation API

This script tests the connectivity between frontend and backend by simulating
the API calls that the frontend would make.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Base URL for the API
API_BASE = "http://127.0.0.1:5000"

def log_test(message, success=True):
    """Log a test result with formatting"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if success:
        print(f"[{timestamp}] ✅ {message}")
    else:
        print(f"[{timestamp}] ❌ {message}")

def log_divider():
    """Print a divider line"""
    print("-" * 80)

def test_server_status():
    """Test if the server is running"""
    log_divider()
    print("TESTING SERVER STATUS")
    log_divider()
    
    try:
        response = requests.get(f"{API_BASE}/", timeout=5)
        if response.status_code == 200:
            log_test(f"Server is running at {API_BASE}")
            
            # Print server info if available
            try:
                if 'application/json' in response.headers.get('Content-Type', ''):
                    data = response.json()
                    if 'endpoints' in data:
                        print("Available endpoints:")
                        for endpoint in data['endpoints']:
                            print(f"  - {endpoint}")
            except:
                pass
            
            return True
        else:
            log_test(f"Server responded with unexpected status code: {response.status_code}", success=False)
            return False
    except requests.exceptions.RequestException as e:
        log_test(f"Cannot connect to server: {e}", success=False)
        return False

def test_routes():
    """Test if the key routes are available"""
    log_divider()
    print("TESTING API ROUTES")
    log_divider()
    
    # Check API documentation endpoint
    try:
        response = requests.get(f"{API_BASE}/api/docs")
        if response.status_code == 200:
            log_test("API documentation available at /api/docs")
        else:
            log_test(f"API documentation not available: {response.status_code}", success=False)
    except Exception as e:
        log_test(f"API docs endpoint error: {e}", success=False)
    
    # Check test endpoint
    try:
        response = requests.get(f"{API_BASE}/test")
        if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
            log_test("Test endpoint is working")
            data = response.json()
            log_test(f"Test endpoint returned {len(data)} fields: {', '.join(data.keys())}")
        else:
            log_test(f"Test endpoint not working: {response.status_code}", success=False)
    except Exception as e:
        log_test(f"Test endpoint error: {e}", success=False)
    
    # Check API routes endpoint
    try:
        response = requests.get(f"{API_BASE}/api/routes")
        if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
            log_test("Routes endpoint is working")
            data = response.json()
            if 'routes' in data:
                print(f"Available routes ({len(data['routes'])}):")
                auth_routes = []
                for route in data['routes']:
                    if '/api/auth/' in route.get('path', ''):
                        auth_routes.append(f"  - {', '.join(route.get('methods', []))} {route.get('path')}")
                
                if auth_routes:
                    print("Authentication routes:")
                    for route in auth_routes:
                        print(route)
                else:
                    log_test("No authentication routes found", success=False)
        else:
            log_test(f"Routes endpoint not working: {response.status_code}", success=False)
    except Exception as e:
        log_test(f"Routes endpoint error: {e}", success=False)

def test_register_user(username, password, email=None):
    """Test user registration"""
    log_divider()
    print(f"TESTING USER REGISTRATION: {username}")
    log_divider()
    
    # Prepare payload
    payload = {
        "username": username,
        "password": password
    }
    
    if email:
        payload["email"] = email
    
    try:
        # Set headers explicitly
        headers = {
            "Content-Type": "application/json"
        }
        
        # Make the request
        response = requests.post(
            f"{API_BASE}/api/auth/register",
            data=json.dumps(payload),
            headers=headers,
            timeout=10
        )
        
        # Print response details
        print(f"Request to: POST {API_BASE}/api/auth/register")
        print(f"Request payload: {json.dumps(payload)}")
        print(f"Response status: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response data: {json.dumps(response_data)}")
        except:
            print(f"Response text: {response.text[:200]}")
        
        # Check if registration was successful
        if response.status_code == 201:
            try:
                data = response.json()
                user = data.get('user', {})
                token = data.get('token')
                
                log_test("Registration successful")
                log_test(f"User ID: {user.get('_id')}")
                log_test(f"Token received: {token[:10]}...{token[-10:]}")
                
                return {
                    "success": True,
                    "user": user,
                    "token": token
                }
            except Exception as e:
                log_test(f"Error parsing response: {e}", success=False)
                return {"success": False, "error": str(e)}
        elif response.status_code == 400 and "exists" in response.text:
            log_test("User already exists, continuing to login test", success=False)
            return {"success": False, "error": "User already exists", "status_code": response.status_code}
        else:
            log_test(f"Registration failed with status code: {response.status_code}", success=False)
            return {"success": False, "error": response.text, "status_code": response.status_code}
    except Exception as e:
        log_test(f"Registration request error: {e}", success=False)
        return {"success": False, "error": str(e)}

def test_login_user(username, password):
    """Test user login"""
    log_divider()
    print(f"TESTING USER LOGIN: {username}")
    log_divider()
    
    # Prepare payload
    payload = {
        "username": username,
        "password": password
    }
    
    try:
        # Set headers explicitly
        headers = {
            "Content-Type": "application/json"
        }
        
        # Make the request
        response = requests.post(
            f"{API_BASE}/api/auth/login",
            data=json.dumps(payload),
            headers=headers,
            timeout=10
        )
        
        # Print response details
        print(f"Request to: POST {API_BASE}/api/auth/login")
        print(f"Request payload: {json.dumps(payload)}")
        print(f"Response status: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response data: {json.dumps(response_data)}")
        except:
            print(f"Response text: {response.text[:200]}")
        
        # Check if login was successful
        if response.status_code == 200:
            try:
                data = response.json()
                user = data.get('user', {})
                token = data.get('token')
                
                log_test("Login successful")
                log_test(f"User ID: {user.get('_id')}")
                log_test(f"Token received: {token[:10]}...{token[-10:]}")
                
                return {
                    "success": True,
                    "user": user,
                    "token": token
                }
            except Exception as e:
                log_test(f"Error parsing response: {e}", success=False)
                return {"success": False, "error": str(e)}
        else:
            log_test(f"Login failed with status code: {response.status_code}", success=False)
            return {"success": False, "error": response.text, "status_code": response.status_code}
    except Exception as e:
        log_test(f"Login request error: {e}", success=False)
        return {"success": False, "error": str(e)}

def test_auth_verification(token):
    """Test token verification"""
    log_divider()
    print("TESTING AUTH VERIFICATION")
    log_divider()
    
    try:
        # Set headers with token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Make the request
        response = requests.get(
            f"{API_BASE}/api/auth/me",
            headers=headers,
            timeout=10
        )
        
        # Print response details
        print(f"Request to: GET {API_BASE}/api/auth/me")
        print(f"Request headers: Authorization: Bearer {token[:10]}...{token[-10:]}")
        print(f"Response status: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response data: {json.dumps(response_data)}")
        except:
            print(f"Response text: {response.text[:200]}")
        
        # Check if verification was successful
        if response.status_code == 200:
            try:
                user = response.json()
                
                log_test("Token verification successful")
                log_test(f"User ID: {user.get('_id')}")
                log_test(f"Username: {user.get('username')}")
                
                return {
                    "success": True,
                    "user": user
                }
            except Exception as e:
                log_test(f"Error parsing response: {e}", success=False)
                return {"success": False, "error": str(e)}
        else:
            log_test(f"Token verification failed with status code: {response.status_code}", success=False)
            return {"success": False, "error": response.text, "status_code": response.status_code}
    except Exception as e:
        log_test(f"Token verification request error: {e}", success=False)
        return {"success": False, "error": str(e)}

def main():
    """Run all tests"""
    log_divider()
    print("FASHION RECOMMENDATION API CONNECTIVITY TEST")
    print(f"Testing API at: {API_BASE}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_divider()
    
    # Test server status
    if not test_server_status():
        print("\nERROR: Server is not running or not accessible.")
        print(f"Make sure the Flask server is running at {API_BASE}")
        print("Run 'python app.py' or 'start_server.bat' to start the server.")
        return
    
    # Test available routes
    test_routes()
    
    # Generate a unique test username
    test_username = f"test_user_{int(time.time())}"
    test_password = "password123"
    test_email = f"{test_username}@example.com"
    
    # Test registration
    register_result = test_register_user(test_username, test_password, test_email)
    
    # If registration fails because user exists, try with a different username
    if not register_result["success"] and register_result.get("error") == "User already exists":
        test_username = f"test_user_{int(time.time())}"
        test_email = f"{test_username}@example.com"
        register_result = test_register_user(test_username, test_password, test_email)
    
    # Get token from registration or try login
    if register_result["success"]:
        token = register_result["token"]
    else:
        # Try login instead
        login_result = test_login_user(test_username, test_password)
        
        if login_result["success"]:
            token = login_result["token"]
        else:
            # Try with guest account as fallback
            log_test("Trying with guest account as fallback")
            login_result = test_login_user("guest", "style123")
            
            if login_result["success"]:
                token = login_result["token"]
            else:
                print("\nERROR: Both registration and login failed.")
                return
    
    # Test token verification
    test_auth_verification(token)
    
    log_divider()
    print("TEST SUMMARY")
    log_divider()
    print(f"Server Status: OK")
    print(f"Authentication Endpoints: {'OK' if token else 'FAILED'}")
    print(f"Connection Status: {'READY' if token else 'NOT READY'}")
    
    if token:
        print("\nThe frontend and backend appear to be correctly connected!")
        print("You can now use the frontend login page to register and login.")
    else:
        print("\nThere are issues with the frontend-backend connection.")
        print("Check the server logs for more details.")

if __name__ == "__main__":
    main() 