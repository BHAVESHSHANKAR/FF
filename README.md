# Fashion Recommendation System

A machine learning-based fashion recommendation system that uses ResNet50 to extract features from fashion images and recommends similar items.

## Features

- Upload fashion images to get recommendations for similar items
- Uses ResNet50 for feature extraction and nearest neighbors for recommendations
- Images are stored in Cloudinary for efficient delivery and management
- Clean and responsive UI for displaying recommendations

## Setup

### Prerequisites

- Python 3.8+
- Cloudinary account (free tier available)

### Installation

1. Clone the repository
2. Install the required dependencies:
```
pip install -r requirements.txt
```

3. Create a `.env` file in the Backend directory with your Cloudinary credentials:
```
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

Replace `your_cloud_name`, `your_api_key`, and `your_api_secret` with your actual Cloudinary credentials.

### Running the Application

1. Start the Flask server:
```
python app.py
```

2. Visit `http://127.0.0.1:5000` in your browser to use the application.

## Directory Structure

```
Backend/
├── app.py                 # Main Flask application
├── cloudinary_utils.py    # Utility functions for Cloudinary operations
├── Images_features.pkl    # Extracted features from fashion images
├── filenames.pkl          # Filenames corresponding to the features
├── templates/             # HTML templates
│   └── index.html         # Main UI
├── images/                # Dataset images
├── uploads/               # Temporary folder for uploaded images
└── .env                   # Environment variables (not committed to git)
```

## How It Works

1. User uploads a fashion image through the web interface
2. The image is temporarily saved and processed using ResNet50 to extract features
3. The image is stored in Cloudinary cloud storage
4. Similar items are found using nearest neighbors algorithm
5. Recommendations are displayed to the user with confidence scores

## Environment Variables

- `CLOUDINARY_CLOUD_NAME`: Your Cloudinary cloud name
- `CLOUDINARY_API_KEY`: Your Cloudinary API key
- `CLOUDINARY_API_SECRET`: Your Cloudinary API secret

## API Documentation with Swagger UI

The API now includes Swagger UI documentation to help you test the API endpoints directly in the browser.

### Setup

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python app.py
   ```

3. Access the Swagger UI at: 
   ```
   http://localhost:5000/api/docs
   ```

### Testing the API

Using Swagger UI, you can:
- Upload images and see the JSON response
- Generate PDF reports
- Test all API endpoints without needing external tools like curl

This helps verify that your API is returning proper JSON responses and working correctly.

### Testing with cURL

You can also test the API using cURL commands:

#### Test the sample JSON endpoint:
```bash
curl -X GET http://localhost:5000/test
```

#### Upload an image for recommendations:
```bash
curl -X POST -F "file=@/path/to/your/image.jpg" http://localhost:5000/upload
```

#### Generate a PDF report:
```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "recommendations": [
    {
      "filename": "shirt1.jpg",
      "category": "Shirt",
      "confidence": 95
    }
  ],
  "uploaded_category": "Shirt",
  "style": "Casual"
}' http://localhost:5000/generate-report --output report.pdf
``` 