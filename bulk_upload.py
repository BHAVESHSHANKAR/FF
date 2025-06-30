import cloudinary
import cloudinary.uploader
import os
import time
from dotenv import load_dotenv

# Load environment variables (optional, using hardcoded credentials)
load_dotenv()

# Cloudinary configuration
cloud_name = "dugq2vlme"
api_key = "934187638771617"
api_secret = "XMTv2996P_ScniDwuxb4qJQuoOU"

cloudinary.config(
    cloud_name=cloud_name,
    api_key=api_key,
    api_secret=api_secret,
    secure=True
)

cloudinary_configured = cloud_name and api_key and api_secret
if not cloudinary_configured:
    print("ERROR: Cloudinary not configured properly.")
    exit(1)

# Your upload_image function (unchanged)
def upload_image(image_path, public_id=None, folder="fashion_uploads", user_id=None):
    try:
        if not cloudinary_configured:
            raise ValueError("Cloudinary is not properly configured")
        
        upload_folder = f"{folder}/{str(user_id).replace('/', '_').replace('.', '_')}" if user_id else folder
        upload_options = {"folder": upload_folder}
        
        if public_id:
            clean_public_id = public_id.replace(' ', '_').replace('/', '_')
            upload_options["public_id"] = clean_public_id
        
        print(f"Uploading image to Cloudinary: {image_path}")
        result = cloudinary.uploader.upload(image_path, **upload_options)
        print(f"Cloudinary upload successful: {result.get('secure_url')}")
        return result
    except Exception as e:
        print(f"Error uploading to Cloudinary: {e}")
        filename = os.path.basename(image_path)
        return {
            "public_id": public_id or os.path.splitext(filename)[0],
            "secure_url": f"/uploads/{filename}",
            "url": f"/uploads/{filename}",
            "original_filename": filename,
            "error": str(e),
            "fallback": True
        }

def bulk_upload_images(image_folder="./images", folder="fashion_uploads", batch_size=50, delay=1):
    """
    Upload all images from the specified folder to Cloudinary.
    
    Args:
        image_folder (str): Local folder containing images (default: ./images).
        folder (str): Cloudinary folder name (default: fashion_uploads).
        batch_size (int): Number of images per batch (default: 50).
        delay (float): Delay between batches in seconds (default: 1).
    """
    image_files = [
        f for f in os.listdir(image_folder)
        if f.lower().endswith((".jpg", ".png", ".jpeg"))
    ]
    total_images = len(image_files)
    print(f"Found {total_images} images to upload.")

    for i in range(0, total_images, batch_size):
        batch = image_files[i:i + batch_size]
        print(f"Uploading batch {i//batch_size + 1}/{(total_images + batch_size - 1)//batch_size}")
        
        for filename in batch:
            file_path = os.path.join(image_folder, filename)
            public_id = os.path.splitext(filename)[0]
            try:
                result = upload_image(file_path, public_id=public_id, folder=folder)
                print(f"Uploaded {filename}: {result.get('secure_url')}")
            except Exception as e:
                print(f"Failed to upload {filename}: {e}")
        
        time.sleep(delay)  # Avoid rate limits

# Run bulk upload
bulk_upload_images(image_folder="./images", folder="fashion_uploads", batch_size=50, delay=1)