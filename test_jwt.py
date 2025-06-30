import requests
import json
import os
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()

# API base URL
BASE_URL = "http://127.0.0.1:5000"

# Utility function to create a test image
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

def test_user_auth(username, password):
    """Test user authentication and token generation"""
    print(f"\n=== Testing Authentication for user: {username} ===\n")
    
    # Step 1: Login with credentials
    print("1. Attempting to login...")
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data
        )
        
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("   Login successful!")
            resp_json = response.json()
            token = resp_json.get("token")
            user = resp_json.get("user")
            
            print(f"   User details: {json.dumps(user, indent=2)}")
            print(f"   Token: {token[:20]}...")
            
            # Step 2: Test the /api/auth/me endpoint with the token
            print("\n2. Testing token with /api/auth/me endpoint...")
            auth_headers = {
                "Authorization": f"Bearer {token}"
            }
            
            me_response = requests.get(
                f"{BASE_URL}/api/auth/me",
                headers=auth_headers
            )
            
            print(f"   Status code: {me_response.status_code}")
            
            if me_response.status_code == 200:
                print("   Authentication successful! User profile retrieved:")
                print(f"   {json.dumps(me_response.json(), indent=2)}")
            else:
                print(f"   Error: {me_response.text}")
            
            # Step 3: Test access to protected /upload endpoint (without actual file first)
            print("\n3. Testing token with /upload endpoint (HEAD request)...")
            
            head_response = requests.head(
                f"{BASE_URL}/upload",
                headers=auth_headers
            )
            
            print(f"   HEAD Status code: {head_response.status_code}")
            
            # Step 4: Test access to protected /upload endpoint (with a real file)
            print("\n4. Testing token with /upload endpoint (with test file)...")
            
            # Create a test file
            test_file = create_test_image()
            
            try:
                # Create a multipart form with the test file
                files = {
                    "file": (test_file, open(test_file, "rb"), "image/jpeg")
                }
                
                print(f"   Sending request to {BASE_URL}/upload with Authorization header")
                print(f"   Authorization: {auth_headers['Authorization'][:15]}...")
                
                # Make request to upload endpoint
                upload_response = requests.post(
                    f"{BASE_URL}/upload",
                    files=files,
                    headers=auth_headers
                )
                
                print(f"   Status code: {upload_response.status_code}")
                
                if upload_response.status_code == 200:
                    print("   Upload endpoint accessible with token!")
                    response_preview = upload_response.text[:100]
                    print(f"   Response preview: {response_preview}...")
                else:
                    print(f"   Error: {upload_response.text}")
                    
                # Check request details that were sent
                print("\n5. Analysis of the upload request:")
                print(f"   Request headers sent: {upload_response.request.headers}")
                
            finally:
                # Clean up test file
                if os.path.exists(test_file):
                    os.remove(test_file)
                    print(f"   Cleaned up test file: {test_file}")
            
            # Step 6: Test with an invalid token
            print("\n6. Testing with invalid token...")
            bad_headers = {
                "Authorization": "Bearer invalid.token.here"
            }
            
            bad_response = requests.get(
                f"{BASE_URL}/api/auth/me",
                headers=bad_headers
            )
            
            print(f"   Status code: {bad_response.status_code}")
            if bad_response.status_code == 401:
                print("   Invalid token correctly rejected!")
            else:
                print(f"   Unexpected result: {bad_response.text}")
                
            return token
        else:
            print(f"   Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   Error: {str(e)}")
        return None

def compare_frontend_headers():
    """Compare the headers being sent from the frontend vs. our test script"""
    print("\n=== Comparing Frontend vs Test Script Headers ===\n")
    
    # Create a sample image file
    test_file = create_test_image()
    
    try:
        # Simulate frontend headers (based on api.ts)
        # This doesn't include Authorization since we identified it was missing
        frontend_headers = {
            # These are headers that browsers typically send
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0 Frontend Simulation"
        }
        
        # Our corrected test headers
        test_headers = {
            "Authorization": "Bearer sample.token.for.testing",
            "Accept": "*/*",
            "User-Agent": "Python Test Script"
        }
        
        print("Frontend Headers (before our fix):")
        print(json.dumps(frontend_headers, indent=2))
        
        print("\nTest Script Headers (with Authorization):")
        print(json.dumps(test_headers, indent=2))
        
        print("\nThe key difference is the Authorization header, which we've added to the frontend.")
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    # Test with different users
    username = "raghava"  # The user with login issues
    password = "ragahva"  # The password that should work
    
    # First try with the provided credentials
    print("Testing with expected credentials...")
    token = test_user_auth(username, password)
    
    if not token:
        print("\nTrying password 'raghava' instead in case it was mistyped...")
        token = test_user_auth(username, "raghava")  # Try alternative password
    
    # Compare frontend vs test script headers
    compare_frontend_headers() 