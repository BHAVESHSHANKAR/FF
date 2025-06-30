import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Cloudinary configuration - using the updated credentials
cloud_name = "dugq2vlme"  # Hardcoded from the new account
api_key = "934187638771617"  # Hardcoded from the new account
api_secret = "XMTv2996P_ScniDwuxb4qJQuoOU"  # Hardcoded from the new account

# Check if configuration is complete
cloudinary_configured = cloud_name and api_key and api_secret

# Only configure if all values are present
if cloudinary_configured:
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True
    )
    print(f"Cloudinary configured with cloud_name: {cloud_name}")
else:
    print("WARNING: Cloudinary not properly configured. Missing environment variables.")
    print(f"Cloud name: {'Set' if cloud_name else 'Not set'}")
    print(f"API key: {'Set' if api_key else 'Not set'}")
    print(f"API secret: {'Set' if api_secret else 'Not set'}")

def upload_image(image_path, public_id=None, folder="fashion_uploads", user_id=None):
    """
    Upload an image to Cloudinary
    
    Args:
        image_path (str): Path to the image file
        public_id (str, optional): Public ID for the image. Defaults to None.
        folder (str, optional): Folder to upload to. Defaults to "fashion_uploads".
        user_id (str, optional): User ID to include in folder path. Defaults to None.
        
    Returns:
        dict: Cloudinary upload response or local file info if Cloudinary is unavailable
    """
    try:
        # Check if Cloudinary is configured
        if not cloudinary_configured:
            raise ValueError("Cloudinary is not properly configured")
            
        # Create a clean folder structure for uploads
        # If user_id is provided, create a user-specific folder
        if user_id:
            # Clean the user_id to avoid issues with special characters
            user_folder = str(user_id).replace('/', '_').replace('.', '_')
            upload_folder = f"{folder}/{user_folder}"
        else:
            upload_folder = folder
        
        # Keep upload options minimal to avoid signature issues
        upload_options = {
            "folder": upload_folder
        }
        
        # Only add public_id if provided and ensure it's clean
        if public_id:
            clean_public_id = public_id.replace(' ', '_').replace('/', '_')
            upload_options["public_id"] = clean_public_id
        
        print(f"Uploading image to Cloudinary: {image_path}")
        print(f"Upload options: {upload_options}")
        
        # Ensure configuration is fresh
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )
        
        # Upload the image
        result = cloudinary.uploader.upload(image_path, **upload_options)
        print(f"Cloudinary upload successful: {result.get('secure_url')}")
        return result
    except Exception as e:
        print(f"Error uploading to Cloudinary: {e}")
        print(f"Error Details: {str(e)}")
        print("Returning local file info instead")
        
        # Return a dict with similar structure to Cloudinary response
        # but using local file path as URL
        if os.path.exists(image_path):
            filename = os.path.basename(image_path)
            return {
                "public_id": public_id or os.path.splitext(filename)[0],
                "secure_url": f"/uploads/{filename}",
                "url": f"/uploads/{filename}",
                "original_filename": filename,
                "error": str(e),
                "fallback": True
            }
        else:
            return {
                "error": f"Image file not found: {image_path}",
                "fallback": True
            }

def delete_image(public_id):
    """
    Delete an image from Cloudinary
    
    Args:
        public_id (str): Public ID of the image to delete
        
    Returns:
        dict: Cloudinary delete response
    """
    try:
        # Check if Cloudinary is configured
        if not cloudinary_configured:
            raise ValueError("Cloudinary is not properly configured")
            
        # Clean the public_id if it contains a full path
        if "/" in public_id:
            public_id = public_id.split("/")[-1]
            
        return cloudinary.uploader.destroy(public_id)
    except Exception as e:
        print(f"Error deleting from Cloudinary: {e}")
        return {"result": "error", "error": str(e)}

def get_image_url(public_id, transformation=None):
    """
    Get the URL for an image
    
    Args:
        public_id (str): Public ID of the image
        transformation (dict, optional): Transformation options. Defaults to None.
        
    Returns:
        str: Image URL
    """
    try:
        # Check if Cloudinary is configured
        if not cloudinary_configured:
            raise ValueError("Cloudinary is not properly configured")
            
        return cloudinary.CloudinaryImage(public_id).build_url(transformation=transformation)
    except Exception as e:
        print(f"Error getting image URL from Cloudinary: {e}")
        # Return a fallback local URL
        return f"/images/{public_id}.jpg"

def get_user_images(user_id, folder="fashion_uploads", max_results=100):
    """
    Get all images for a specific user
    
    Args:
        user_id (str): User ID
        folder (str, optional): Base folder name. Defaults to "fashion_uploads".
        max_results (int, optional): Maximum number of results to return. Defaults to 100.
        
    Returns:
        list: List of image resources
    """
    try:
        # Check if Cloudinary is configured
        if not cloudinary_configured:
            raise ValueError("Cloudinary is not properly configured")
        
        # Clean the user_id to avoid issues with special characters
        user_folder = str(user_id).replace('/', '_').replace('.', '_')
        # User-specific folder path
        search_folder = f"{folder}/{user_folder}"
        
        # Get all resources in the user's folder
        result = cloudinary.api.resources(
            type="upload",
            prefix=search_folder,
            max_results=max_results
        )
        
        return result.get('resources', [])
    except Exception as e:
        print(f"Error getting user images from Cloudinary: {e}")
        return [] 