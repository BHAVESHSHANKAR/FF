import numpy as np
import pickle as pkl
import tensorflow as tf
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.preprocessing import image
from tensorflow.keras.layers import GlobalMaxPool2D
from sklearn.neighbors import NearestNeighbors
import os
import re
import io
import json
from numpy.linalg import norm
from flask import Flask, request, jsonify, send_from_directory, send_file, make_response
from flask_cors import CORS
from dotenv import load_dotenv
import cloudinary_utils as cloud
import time
from datetime import datetime
from flask_swagger_ui import get_swaggerui_blueprint

# Import authentication and database modules
from auth import create_user, authenticate_user, generate_token, get_user_by_id
from middleware import auth_required
from models import save_uploaded_image, get_user_images, get_image_by_id, delete_image

# Import PDF generation library (PyFPDF which doesn't have additional dependencies)
try:
    from fpdf import FPDF
except ImportError:
    print("FPDF library not installed. PDF reports will not be available.")
    print("To install: pip install fpdf")

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Configure CORS with specific settings
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "DELETE"], "allow_headers": ["Content-Type", "Authorization"]}})

# Set debug mode for detailed error messages
app.debug = True

# Configure Swagger UI
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI
API_URL = '/swagger.json'  # Our API url - changed from /static/swagger.json to /swagger.json

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Fashion Recommendation API"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

try:
    Image_features = pkl.load(open("Images_features.pkl", "rb"))
    filenames = pkl.load(open("filenames.pkl", "rb"))

    model = ResNet50(weights="imagenet", include_top=False, input_shape=(224, 224, 3))
    model.trainable = False
    model = tf.keras.models.Sequential([model, GlobalMaxPool2D()])

    neighbors = NearestNeighbors(n_neighbors=6, algorithm="brute", metric="euclidean")
    neighbors.fit(Image_features)
except Exception as e:
    print(f"Warning: Could not load ML models: {e}")
    print("Fashion recommendation functionality may be limited")
    
    # Create dummy data for testing
    Image_features = []
    filenames = []
    model = None
    neighbors = None

# Define fashion categories (mapping patterns in filenames to categories)
category_patterns = {
    "tshirt": "T-Shirt",
    "shirt": "Shirt",
    "jeans": "Jeans",
    "trouser": "Trousers",
    "pant": "Pants",
    "dress": "Dress",
    "skirt": "Skirt",
    "jacket": "Jacket",
    "coat": "Coat",
    "sweater": "Sweater",
    "hoodie": "Hoodie",
    "shorts": "Shorts",
    "top": "Top",
    "blouse": "Blouse",
    "formal": "Formal Wear",
    "casual": "Casual Wear",
    "shoe": "Shoes",
    "sneaker": "Sneakers",
    "boot": "Boots",
    "sandal": "Sandals",
    "accessory": "Accessories",
    "bag": "Bags",
    "handbag": "Handbags",
    "hat": "Hats",
    "scarf": "Scarves",
    "watch": "Watches",
    "jewelry": "Jewelry"
}

def get_category_from_filename(filename):
    """Extract category from filename"""
    filename_lower = filename.lower()
    
    # Default category if none is found
    category = "Fashion Item"
    
    for pattern, cat_name in category_patterns.items():
        if pattern in filename_lower:
            category = cat_name
            break
            
    return category

def extract_features_from_images(image_path, model):
    img = image.load_img(image_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_expand_dim = np.expand_dims(img_array, axis=0)
    img_preprocess = preprocess_input(img_expand_dim)
    result = model.predict(img_preprocess, verbose=0).flatten()
    norm_result = result / norm(result)
    return norm_result

def calculate_confidence(distance):
    """Convert distance to confidence score (0-100%)"""
    # Lower distance means higher confidence
    # We use an exponential decay function to convert distance to confidence
    # Max confidence is 100%, min is around 50%
    return max(50, round(100 * np.exp(-distance * 0.5)))

def generate_pdf_report(recommendations, category, style):
    """Generate a PDF report for the style analysis"""
    try:
        # Create PDF instance
        pdf = FPDF()
        pdf.add_page()
        
        # Set font and styling
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Fashion Style Analysis Report", 0, 1, "C")
        
        # Add date
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, "C")
        
        # Add uploaded image info
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Analyzed Item", 0, 1)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Category: {category}", 0, 1)
        pdf.cell(0, 10, f"Detected Style: {style}", 0, 1)
        
        # Add recommendations
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 15, "Recommended Similar Items", 0, 1)
        
        pdf.set_font("Arial", "", 12)
        for i, rec in enumerate(recommendations):
            pdf.cell(0, 10, f"{i+1}. {rec['category']} (Confidence: {rec['confidence']}%)", 0, 1)
        
        # Add styling tips
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 15, "Style Tips", 0, 1)
        
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"1. {category} items work well with complementary accessories.", 0, 1)
        pdf.cell(0, 10, f"2. Consider pairing with similar styled items for a cohesive look.", 0, 1)
        pdf.cell(0, 10, f"3. This style works well for both casual and formal occasions.", 0, 1)
        
        # Add footer
        pdf.set_y(-20)
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 10, "Fashion Recommendation System - www.fashionrec.ai", 0, 0, "C")
        
        # Get the PDF as bytes
        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)
        
        return pdf_output
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None

@app.route('/swagger.json')
def swagger_json():
    """Serve the swagger definition file"""
    # Get the absolute path to the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    swagger_path = os.path.join(current_dir, 'swagger.json')
    return send_file(swagger_path, mimetype='application/json')

@app.route("/", methods=["GET"])
def index():
    """Root endpoint - for server status checking"""
    try:
        return send_file("templates/index.html")  
    except Exception as e:
        # Return JSON response if HTML file is not found
        return jsonify({
            "status": "online",
            "message": "Fashion Recommendation API is running",
            "endpoints": [
                "/api/auth/register - Register a new user",
                "/api/auth/login - Login existing user", 
                "/api/auth/me - Get current user details",
                "/upload - Upload a clothing image for analysis",
                "/api/images - Get user uploaded images",
                "/test - Test endpoint"
            ]
        })

# Authentication Routes
@app.route("/api/auth/register", methods=["POST"])
def register():
    """Register a new user"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Check required fields
        required_fields = ["username", "password"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create user
        user = create_user(
            username=data["username"],
            password=data["password"],
            email=data.get("email"),
            name=data.get("name")
        )
        
        if isinstance(user, dict) and "error" in user:
            return jsonify(user), 400
        
        # Generate token
        token = generate_token(user["_id"])
        
        return jsonify({
            "user": user,
            "token": token
        }), 201
    except Exception as e:
        print(f"Error in register route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    """Login an existing user"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Check required fields
        required_fields = ["username", "password"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Authenticate user
        user = authenticate_user(data["username"], data["password"])
        
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Generate token
        token = generate_token(user["_id"])
        
        return jsonify({
            "user": user,
            "token": token
        })
    except Exception as e:
        print(f"Error in login route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/me", methods=["GET"])
@auth_required
def get_me():
    """Get current user (requires authentication)"""
    try:
        # User is already loaded in the request by the auth_required decorator
        return jsonify(request.user)
    except Exception as e:
        print(f"Error in get_me route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/upload", methods=["POST"])
@auth_required
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400
        
        # Create uploads directory if it doesn't exist
        os.makedirs("uploads", exist_ok=True)
        
        # Generate a unique filename with timestamp to avoid collisions
        timestamp = int(time.time())
        original_filename = file.filename
        file_parts = os.path.splitext(original_filename)
        sanitized_filename = f"upload_{timestamp}{file_parts[1]}"
        
        # Save temporarily to process with the model
        upload_path = os.path.join("uploads", sanitized_filename)
        file.save(upload_path)
        
        print(f"File saved locally at: {upload_path}")
        
        # Extract features for recommendation (skip if model isn't loaded)
        recommendations = []
        
        if model is not None and neighbors is not None:
            input_img_features = extract_features_from_images(upload_path, model)
            distances, indices = neighbors.kneighbors([input_img_features])
            
            # Prepare recommendations with additional data
            for i in range(1, min(6, len(indices[0]))):  # Skip the first one as it's usually the same image
                idx = indices[0][i]
                filename = os.path.basename(filenames[idx])
                distance = distances[0][i]
                confidence = calculate_confidence(distance)
                category = get_category_from_filename(filename)
                
                recommendations.append({
                    "filename": filename,
                    "category": category,
                    "confidence": confidence
                })
        
        # Upload to Cloudinary using our utility module with user_id
        public_id = f"upload_{timestamp}"
        user_id = request.user["_id"]
        
        # Default to local URL in case Cloudinary fails
        image_url = f"/uploads/{sanitized_filename}"
        
        try:
            print(f"Attempting Cloudinary upload for user {user_id}")
            cloudinary_upload = cloud.upload_image(
                upload_path, 
                public_id=public_id,
                user_id=user_id
            )
            
            # Only use Cloudinary URL if upload was successful (not a fallback)
            if 'secure_url' in cloudinary_upload and not cloudinary_upload.get('fallback', False):
                image_url = cloudinary_upload['secure_url']
                print(f"Using Cloudinary URL: {image_url}")
            else:
                print(f"Using local URL as fallback: {image_url}")
                
        except Exception as cloud_error:
            print(f"Cloudinary upload error: {cloud_error}")
        
        # Get the category of the uploaded image
        uploaded_category = get_category_from_filename(original_filename)
        
        try:
            # Save to MongoDB
            image_data = save_uploaded_image(
                user_id=user_id,
                filename=original_filename,  # Store original filename for display
                image_url=image_url,
                category=uploaded_category,
                recommendations=recommendations
            )
            image_id = image_data["_id"]
            print(f"Image saved to database with ID: {image_id}")
        except Exception as db_error:
            print(f"Database error: {db_error}")
            # Use a placeholder ID if database save fails
            image_id = f"temp_id_{timestamp}"
        
        return jsonify({
            "uploaded_image": original_filename,
            "uploaded_category": uploaded_category,
            "image_url": image_url,
            "recommendations": recommendations,
            "image_id": image_id,
            "status": "success"
        })
    except Exception as e:
        print(f"Error in upload_file route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/images', methods=['GET'])
@auth_required
def get_user_uploaded_images():
    """Get all images uploaded by the current user"""
    try:
        user_id = request.user["_id"]
        
        # Get pagination parameters
        limit = int(request.args.get('limit', 10))
        skip = int(request.args.get('skip', 0))
        
        # Get images from MongoDB
        images = get_user_images(user_id, limit, skip)
        
        return jsonify({
            "images": images,
            "count": len(images)
        })
    except Exception as e:
        print(f"Error in get_user_uploaded_images route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/images/<image_id>', methods=['GET'])
@auth_required
def get_image(image_id):
    """Get a specific image by ID"""
    try:
        image = get_image_by_id(image_id)
        
        if not image:
            return jsonify({"error": "Image not found"}), 404
        
        # Check if user is authorized to view this image
        if image["user_id"] != request.user["_id"]:
            return jsonify({"error": "Unauthorized"}), 403
        
        return jsonify(image)
    except Exception as e:
        print(f"Error in get_image route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/images/<image_id>', methods=['DELETE'])
@auth_required
def delete_user_image(image_id):
    """Delete an image by ID"""
    try:
        user_id = request.user["_id"]
        
        # Delete image
        result = delete_image(image_id, user_id)
        
        if not result:
            return jsonify({"error": "Image not found or already deleted"}), 404
        
        return jsonify({"message": "Image deleted successfully"})
    except Exception as e:
        print(f"Error in delete_user_image route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate-report', methods=['POST'])
@auth_required
def generate_report():
    """Generate a PDF report for the style analysis"""
    try:
        # Get data from request
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract necessary info
        recommendations = data.get('recommendations', [])
        category = data.get('uploaded_category', 'Fashion Item')
        style = data.get('style', 'Casual')
        
        # Generate PDF
        pdf_bytes = generate_pdf_report(recommendations, category, style)
        
        if not pdf_bytes:
            return jsonify({"error": "Failed to generate PDF report"}), 500
        
        # Create response with PDF
        response = make_response(pdf_bytes.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=fashion-report-{int(time.time())}.pdf'
        
        return response
    
    except Exception as e:
        print(f"Error in generate_report: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory("uploads", filename)

@app.route('/images/<filename>')
def dataset_image(filename):
    return send_from_directory("images", filename)

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint that returns a JSON response without requiring file upload"""
    sample_response = {
        "uploaded_image": "sample_tshirt.jpg",
        "uploaded_category": "T-Shirt",
        "image_url": "https://res.cloudinary.com/sample/image/upload/sample_tshirt.jpg",
        "recommendations": [
            {
                "filename": "blue_tshirt.jpg",
                "category": "T-Shirt",
                "confidence": 95
            },
            {
                "filename": "red_tshirt.jpg",
                "category": "T-Shirt",
                "confidence": 87
            },
            {
                "filename": "black_tshirt.jpg",
                "category": "T-Shirt",
                "confidence": 82
            }
        ],
        "status": "success"
    }
    return jsonify(sample_response)

@app.route('/api/routes')
def list_routes():
    """List all available routes in the application"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "methods": list(rule.methods),
            "path": str(rule)
        })
    return jsonify({"routes": routes})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found", "message": str(error)}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Server error", "message": str(error)}), 500

if __name__ == "__main__":
    # Create uploads directory if it doesn't exist
    os.makedirs("uploads", exist_ok=True)
    
    # Print all available routes
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"{', '.join(rule.methods)} {rule.rule}")
    
    # Run the app
    app.run(debug=True)
