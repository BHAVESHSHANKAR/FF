from datetime import datetime
from bson.objectid import ObjectId
from database import uploaded_images_collection, users_collection
import cloudinary_utils as cloud

def save_uploaded_image(user_id, filename, image_url, category, recommendations=None):
    """
    Save uploaded image metadata to MongoDB
    
    Args:
        user_id (str): User ID
        filename (str): Original filename
        image_url (str): Cloudinary URL
        category (str): Category of the image
        recommendations (list, optional): List of recommended items. Defaults to None.
        
    Returns:
        dict: Saved image document
    """
    # Create image document
    image_data = {
        "user_id": user_id,
        "filename": filename,
        "image_url": image_url,
        "category": category,
        "recommendations": recommendations or [],
        "uploaded_at": datetime.utcnow()
    }
    
    # Insert into database
    result = uploaded_images_collection.insert_one(image_data)
    
    # Return document with string ID
    image_data["_id"] = str(result.inserted_id)
    
    return image_data

def get_user_images(user_id, limit=10, skip=0):
    """
    Get images uploaded by a specific user
    
    Args:
        user_id (str): User ID
        limit (int, optional): Maximum number of results. Defaults to 10.
        skip (int, optional): Number of results to skip (for pagination). Defaults to 0.
        
    Returns:
        list: List of image documents
    """
    # Query database for user's images
    cursor = uploaded_images_collection.find(
        {"user_id": user_id}
    ).sort(
        "uploaded_at", -1  # Sort by upload date (newest first)
    ).skip(skip).limit(limit)
    
    # Convert to list and format IDs
    images = []
    for image in cursor:
        image["_id"] = str(image["_id"])
        images.append(image)
    
    return images

def get_image_by_id(image_id):
    """
    Get image by ID
    
    Args:
        image_id (str): Image ID
        
    Returns:
        dict: Image document or None
    """
    try:
        # Try to convert to ObjectId if it's not already for MongoDB compatibility
        try:
            if not image_id.startswith("temp_id_"):  # Don't convert temporary IDs
                image_id_obj = ObjectId(image_id)
            else:
                image_id_obj = image_id
        except:
            # If conversion fails, use as-is (for in-memory database)
            image_id_obj = image_id
            
        image = uploaded_images_collection.find_one({"_id": image_id_obj})
        
        if image:
            image["_id"] = str(image["_id"])
            
        return image
    except Exception as e:
        print(f"Error getting image: {e}")
        return None

def delete_image(image_id, user_id):
    """
    Delete an image and its metadata
    
    Args:
        image_id (str): Image ID
        user_id (str): User ID (for authorization)
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        # Try to convert to ObjectId if it's not already for MongoDB compatibility
        try:
            if not image_id.startswith("temp_id_"):  # Don't convert temporary IDs
                image_id_obj = ObjectId(image_id)
            else:
                image_id_obj = image_id
        except:
            # If conversion fails, use as-is (for in-memory database)
            image_id_obj = image_id
            
        # Get image document
        image = uploaded_images_collection.find_one({
            "_id": image_id_obj,
            "user_id": user_id  # Ensure user owns the image
        })
        
        if not image:
            return False
        
        # Delete from Cloudinary (extract public_id from URL)
        # We just delete the document from MongoDB even if Cloudinary delete fails
        try:
            # The public_id is usually the part after the last slash and before the file extension
            image_url = image.get("image_url", "")
            if image_url:
                # Example: https://res.cloudinary.com/demo/image/upload/v1234/folder/public_id.jpg
                public_id = image_url.split("/")[-1].split(".")[0]
                cloud.delete_image(public_id)
        except Exception as e:
            print(f"Error deleting image from Cloudinary: {e}")
        
        # Delete from MongoDB
        result = uploaded_images_collection.delete_one({
            "_id": image_id_obj,
            "user_id": user_id
        })
        
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting image: {e}")
        return False 