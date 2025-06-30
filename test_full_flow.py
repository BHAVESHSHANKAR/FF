#!/usr/bin/env python
"""
Test the full authentication and upload flow
This script tests:
1. User registration
2. User login
3. Getting user info
4. Image upload with authentication
"""

import requests
import json
import os
import time
import random
import string
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API base URL
BASE_URL = "http://127.0.0.1:5000"

def generate_random_username(length=8):
    """Generate a random username for testing"""
    return 'test_' + ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

def create_test_image(filename="test_image.jpg", size=(100, 100)):
    """Create a simple test image for upload testing"""
    try:
        from PIL import Image
        # Create a small colored image
        img = Image.new('RGB', size, color=(73, 109, 137))
        img.save(filename)
        print(f"Created test image: {filename}")
        return filename
    except ImportError:
        # If PIL is not available, create a simple binary file
        with open(filename, "wb") as f:
            f.write(b"Test image data " * 100)  # Create some content
        print(f"Created dummy test file: {filename}")
        return filename

def test_registration(username, password):
    """Test user registration"""
    print(f"\n=== 1. Testing User Registration for {username} ===\n")
    
    registration_data = {
        "username": username,
        "password": password,
        "email": f"{username}@example.com",
        "name": f"Test User {username.capitalize()}"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=registration_data
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code in (200, 201):
            print("Registration successful!")
            resp_json = response.json()
            token = resp_json.get("token")
            user = resp_json.get("user")
            
            print(f"User details: {json.dumps(user, indent=2)}")
            if token:
                print(f"Token: {token[:20]}...")
            
            return token, user
        else:
            print(f"Registration failed: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return None, None

def test_login(username, password):
    """Test user login"""
    print(f"\n=== 2. Testing User Login for {username} ===\n")
    
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("Login successful!")
            resp_json = response.json()
            token = resp_json.get("token")
            user = resp_json.get("user")
            
            print(f"User details: {json.dumps(user, indent=2)}")
            print(f"Token: {token[:20]}...")
            
            return token, user
        else:
            print(f"Login failed: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return None, None

def test_get_user_info(token):
    """Test getting user info with token"""
    if not token:
        print("No token available, skipping user info test")
        return False
        
    print("\n=== 3. Testing Get User Info ===\n")
    
    auth_headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers=auth_headers
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("Authentication successful! User profile retrieved:")
            print(f"{json.dumps(response.json(), indent=2)}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_image_upload(token):
    """Test image upload with authentication"""
    if not token:
        print("No token available, skipping image upload test")
        return False
        
    print("\n=== 4. Testing Image Upload with Authentication ===\n")
    
    # Create a test image
    test_file = create_test_image()
    
    auth_headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        # Create multipart form with test file
        files = {
            "file": (test_file, open(test_file, "rb"), "image/jpeg")
        }
        
        print(f"Sending request to {BASE_URL}/upload with Authorization header")
        print(f"Authorization: {auth_headers['Authorization'][:20]}...")
        
        # Make request to upload endpoint
        response = requests.post(
            f"{BASE_URL}/upload",
            files=files,
            headers=auth_headers
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("Upload successful!")
            print(f"Response preview: {response.text[:200]}...")
            
            # Parse the response to get the image URL and recommendations
            resp_json = response.json()
            image_url = resp_json.get("image_url")
            recommendations = resp_json.get("recommendations", [])
            
            print(f"Image URL: {image_url}")
            print(f"Recommendations: {len(recommendations)} items found")
            
            return True
        else:
            print(f"Upload failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"Cleaned up test file: {test_file}")

def test_user_images(token):
    """Test getting user's uploaded images"""
    if not token:
        print("No token available, skipping user images test")
        return False
        
    print("\n=== 5. Testing Get User Images ===\n")
    
    auth_headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/images",
            headers=auth_headers
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("Successfully retrieved user images!")
            resp_json = response.json()
            images = resp_json.get("images", [])
            count = resp_json.get("count", 0)
            
            print(f"Found {count} images")
            
            if images and len(images) > 0:
                print(f"First image preview: {json.dumps(images[0], indent=2)}")
            
            return True
        else:
            print(f"Failed to get user images: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def run_full_test():
    """Run the full authentication and upload flow test"""
    print("="*50)
    print("STARTING FULL AUTHENTICATION AND UPLOAD TEST")
    print("="*50)
    
    # Generate a random username to avoid conflicts
    username = generate_random_username()
    password = "testpassword123"
    
    print(f"Testing with credentials: username='{username}', password='{password}'")
    
    # Step 1: Register a new user
    token, user = test_registration(username, password)
    
    if not token:
        # Try logging in with an existing account if registration fails
        print("\nTrying to login with 'raghava' instead...")
        token, user = test_login("raghava", "ragahva")
    
    if not token:
        print("\n❌ TEST FAILED: Could not get a valid authentication token")
        return False
    
    # Step 2: Get user info
    user_info_success = test_get_user_info(token)
    
    # Step 3: Upload an image
    upload_success = test_image_upload(token)
    
    # Step 4: Get user images
    images_success = test_user_images(token)
    
    # Print summary
    print("\n"+"="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"✓ Authentication: {'Success' if token else 'Failed'}")
    print(f"✓ User Info: {'Success' if user_info_success else 'Failed'}")
    print(f"✓ Image Upload: {'Success' if upload_success else 'Failed'}")
    print(f"✓ User Images: {'Success' if images_success else 'Failed'}")
    
    overall_success = token and user_info_success and upload_success and images_success
    print("\n"+"="*50)
    print(f"OVERALL TEST: {'SUCCESS ✅' if overall_success else 'FAILED ❌'}")
    print("="*50)
    
    return overall_success

if __name__ == "__main__":
    run_full_test() 