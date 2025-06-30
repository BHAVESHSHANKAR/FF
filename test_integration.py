import requests
import json
import sys

API_BASE = "http://127.0.0.1:5000"

def test_routes():
    """Test available routes"""
    print("\n=== Testing Available Routes ===")
    
    # Test root endpoint
    try:
        response = requests.get(f"{API_BASE}/")
        print(f"Root endpoint: {response.status_code}")
    except Exception as e:
        print(f"Root endpoint error: {e}")
    
    # Check API documentation endpoint
    try:
        response = requests.get(f"{API_BASE}/api/docs")
        print(f"API docs endpoint: {response.status_code}")
    except Exception as e:
        print(f"API docs endpoint error: {e}")
    
    # Check if the server returns the correct content type
    try:
        response = requests.get(f"{API_BASE}/test")
        print(f"Test endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"Content type: {response.headers.get('Content-Type')}")
    except Exception as e:
        print(f"Test endpoint error: {e}")

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("\n=== Testing Auth Integration ===")
    
    # Test variables
    test_username = "test_integration_user"
    test_password = "password123"
    test_email = "test@example.com"
    
    # 1. Test registration
    print("\n1. Testing user registration...")
    try:
        # Print the full URL we're trying to access
        full_url = f"{API_BASE}/api/auth/register"
        print(f"POST {full_url}")
        
        # Set headers explicitly
        headers = {
            "Content-Type": "application/json"
        }
        
        # Prepare payload
        payload = {
            "username": test_username,
            "password": test_password,
            "email": test_email
        }
        
        print(f"Request payload: {json.dumps(payload)}")
        
        # Register a new user
        register_response = requests.post(
            full_url,
            json=payload,
            headers=headers
        )
        
        print(f"Response status code: {register_response.status_code}")
        print(f"Response headers: {dict(register_response.headers)}")
        
        if register_response.status_code == 201:
            print(f"✅ Registration successful! Status code: {register_response.status_code}")
            response_data = register_response.json()
            print(f"Response data: {json.dumps(response_data)}")
            print(f"User data: {response_data['user']['username']}")
            token = response_data['token']
            print(f"Token received: {token[:10]}...{token[-10:]}")
        else:
            print(f"⚠️ Registration returned status code: {register_response.status_code}")
            print(f"Response: {register_response.text}")
            # If user already exists, continue with login test
            if register_response.status_code == 400 and "exists" in register_response.text:
                print("User might already exist, continuing with login test")
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
    
    # 2. Test login
    print("\n2. Testing user login...")
    try:
        # Print the full URL we're trying to access
        full_url = f"{API_BASE}/api/auth/login"
        print(f"POST {full_url}")
        
        # Set headers explicitly
        headers = {
            "Content-Type": "application/json"
        }
        
        # Prepare payload
        payload = {
            "username": test_username,
            "password": test_password
        }
        
        print(f"Request payload: {json.dumps(payload)}")
        
        # Login with the test user
        login_response = requests.post(
            full_url,
            json=payload,
            headers=headers
        )
        
        print(f"Response status code: {login_response.status_code}")
        print(f"Response headers: {dict(login_response.headers)}")
        
        if login_response.status_code == 200:
            print(f"✅ Login successful! Status code: {login_response.status_code}")
            response_data = login_response.json()
            print(f"Response data: {json.dumps(response_data)}")
            token = response_data['token']
            print(f"Token received: {token[:10]}...{token[-10:]}")
            
            # Save token for next test
            auth_token = token
        else:
            print(f"❌ Login failed with status code: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return
    
    # 3. Test auth/me endpoint
    print("\n3. Testing user info endpoint...")
    try:
        # Print the full URL we're trying to access
        full_url = f"{API_BASE}/api/auth/me"
        print(f"GET {full_url}")
        
        # Set headers explicitly with token
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        print(f"Request headers: {headers}")
        
        # Get user info with token
        me_response = requests.get(
            full_url,
            headers=headers
        )
        
        print(f"Response status code: {me_response.status_code}")
        print(f"Response headers: {dict(me_response.headers)}")
        
        if me_response.status_code == 200:
            print(f"✅ Auth verification successful! Status code: {me_response.status_code}")
            print(f"User info: {me_response.json()}")
        else:
            print(f"❌ Auth verification failed with status code: {me_response.status_code}")
            print(f"Response: {me_response.text}")
    except Exception as e:
        print(f"❌ Auth verification test failed: {e}")
    
    print("\n=== Auth Integration Test Complete ===")

if __name__ == "__main__":
    # First check if server is running
    try:
        health_check = requests.get(f"{API_BASE}/")
        print(f"Server is running at {API_BASE}")
        
        # Test available routes
        test_routes()
        
        # Run integration tests
        test_auth_endpoints()
    except requests.ConnectionError:
        print(f"❌ Cannot connect to server at {API_BASE}")
        print("Please make sure the Flask app is running before running this test") 