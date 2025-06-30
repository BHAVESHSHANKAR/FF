import numpy as np
import pickle as pkl
import tensorflow as tf
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.preprocessing import image
from tensorflow.keras.layers import GlobalMaxPool2D
import os
from numpy.linalg import norm

# Load all image filenames from the dataset
filenames = [os.path.join("images", file) for file in os.listdir("images") if file.endswith(".jpg")]

# Load ResNet50 model
model = ResNet50(weights="imagenet", include_top=False, input_shape=(224, 224, 3))
model.trainable = False
model = tf.keras.models.Sequential([model, GlobalMaxPool2D()])

# Feature extraction function
def extract_features_from_images(image_path, model):
    try:
        img = image.load_img(image_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_expand_dim = np.expand_dims(img_array, axis=0)
        img_preprocess = preprocess_input(img_expand_dim)
        result = model.predict(img_preprocess).flatten()
        norm_result = result / norm(result)
        return norm_result
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

# Extract features for all images
image_features = []
for file in filenames:
    features = extract_features_from_images(file, model)
    if features is not None:
        image_features.append(features)

# Save to pickle files
pkl.dump(filenames, open("filenames.pkl", "wb"))
pkl.dump(image_features, open("Images_features.pkl", "wb"))

print("Preprocessing complete. Files saved: filenames.pkl, Images_features.pkl")