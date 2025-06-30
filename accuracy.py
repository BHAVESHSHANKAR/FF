# import numpy as np
# import pickle as pkl
# from sklearn.neighbors import NearestNeighbors
# import pandas as pd
# import os

# # Load precomputed data
# try:
#     image_features = pkl.load(open("Images_features.pkl", "rb"))
#     filenames = pkl.load(open("filenames.pkl", "rb"))
# except FileNotFoundError as e:
#     print(f"Error: {e}. Ensure Images_features.pkl and filenames.pkl are in the current directory.")
#     exit(1)

# # Load metadata from styles.csv
# try:
#     styles_df = pd.read_csv("styles.csv", on_bad_lines="skip")  # Skip malformed rows
#     styles_df["image"] = styles_df["id"].astype(str) + ".jpg"  # Match filenames (e.g., "10000.jpg")
# except FileNotFoundError as e:
#     print(f"Error: {e}. Ensure styles.csv is in the current directory.")
#     exit(1)

# # Set up NearestNeighbors (same as in app.py)
# neighbors = NearestNeighbors(n_neighbors=6, algorithm="brute", metric="euclidean")
# neighbors.fit(image_features)

# # Function to evaluate recommendation accuracy
# def calculate_recommendation_accuracy(features, filenames, styles_df, neighbors, num_samples=None):
#     if num_samples is None or num_samples > len(filenames):
#         num_samples = len(filenames)
    
#     correct = 0
#     total_valid = 0
    
#     for i in range(num_samples):
#         # Input image features and filename
#         input_features = features[i]
#         input_filename = filenames[i]
#         input_image_name = os.path.basename(input_filename)  # e.g., "10000.jpg"

#         # Get ground truth category
#         input_category = styles_df[styles_df["image"] == input_image_name]["masterCategory"].values
#         if len(input_category) == 0:
#             continue  # Skip if no metadata found
#         input_category = input_category[0]
#         total_valid += 1

#         # Find nearest neighbors
#         distances, indices = neighbors.kneighbors([input_features])
#         recommended_indices = indices[0][1:6]  # Skip the first (self-match), take next 5
        
#         # Check category matches
#         matches = 0
#         for idx in recommended_indices:
#             rec_filename = filenames[idx]
#             rec_image_name = os.path.basename(rec_filename)
#             rec_category = styles_df[styles_df["image"] == rec_image_name]["masterCategory"].values
#             if len(rec_category) > 0 and rec_category[0] == input_category:
#                 matches += 1
        
#         # Consider "correct" if at least 3 out of 5 match
#         if matches >= 3:
#             correct += 1

#     # Calculate accuracy
#     if total_valid == 0:
#         return 0.0
#     accuracy = (correct / total_valid) * 100
#     return accuracy

# num_samples = 100  
# accuracy = calculate_recommendation_accuracy(image_features, filenames, styles_df, neighbors, num_samples=num_samples)

# print(f"Recommendation Accuracy (based on category matching, {num_samples} samples): {accuracy:.2f}%")
import numpy as np
import pickle as pkl
from sklearn.neighbors import NearestNeighbors
import pandas as pd
import os
import random

# Load precomputed data
try:
    image_features = pkl.load(open("Images_features.pkl", "rb"))
    filenames = pkl.load(open("filenames.pkl", "rb"))
    print(f"Loaded {len(image_features)} features and {len(filenames)} filenames")
except FileNotFoundError as e:
    print(f"Error: {e}. Ensure Images_features.pkl and filenames.pkl are in the current directory.")
    exit(1)

# Load metadata from styles.csv
try:
    styles_df = pd.read_csv("styles.csv", on_bad_lines="skip")
    styles_df["image"] = styles_df["id"].astype(str) + ".jpg"
    print(f"Loaded {len(styles_df)} rows from styles.csv")
except FileNotFoundError as e:
    print(f"Error: {e}. Ensure styles.csv is in the current directory.")
    exit(1)

# Set up NearestNeighbors
neighbors = NearestNeighbors(n_neighbors=6, algorithm="brute", metric="euclidean")
neighbors.fit(image_features)

# Function to evaluate recommendation accuracy for 10 specific images
def calculate_recommendation_accuracy_for_10(features, filenames, styles_df, neighbors, indices=None):
    if indices is None:
        # Randomly select 10 unique indices
        indices = random.sample(range(len(filenames)), 10)
    elif len(indices) != 10:
        print(f"Expected 10 indices, got {len(indices)}. Using random selection instead.")
        indices = random.sample(range(len(filenames)), 10)

    correct = 0
    total_valid = 0
    
    for i in indices:
        input_features = features[i]
        input_filename = filenames[i]
        input_image_name = os.path.basename(input_filename)

        # Get ground truth category
        input_category = styles_df[styles_df["image"] == input_image_name]["masterCategory"].values
        if len(input_category) == 0:
            print(f"No category found for {input_image_name}, skipping")
            continue
        input_category = input_category[0]
        total_valid += 1

        # Find nearest neighbors
        distances, indices = neighbors.kneighbors([input_features])
        recommended_indices = indices[0][1:6]  # Skip the first (self-match)
        print(f"Image {i}: Input {input_image_name}, Category {input_category}")

        # Check category matches
        matches = 0
        for idx in recommended_indices:
            rec_filename = filenames[idx]
            rec_image_name = os.path.basename(rec_filename)
            rec_category = styles_df[styles_df["image"] == rec_image_name]["masterCategory"].values
            if len(rec_category) > 0:
                if rec_category[0] == input_category:
                    matches += 1
                print(f"  Rec {rec_image_name}: Category {rec_category[0]}, Match: {rec_category[0] == input_category}")
            else:
                print(f"  Rec {rec_image_name}: No category found")

        # Consider "correct" if at least 3 out of 5 match
        if matches >= 3:
            correct += 1
            print(f"  Result: Correct (matches: {matches})")
        else:
            print(f"  Result: Incorrect (matches: {matches})")

    # Calculate accuracy
    if total_valid == 0:
        return 0.0, 0, 0
    accuracy = (correct / total_valid) * 100
    return accuracy, total_valid, correct

# Evaluate accuracy for 10 random images
indices = None  # Use random selection; replace with specific indices if desired
accuracy, total_valid, correct = calculate_recommendation_accuracy_for_10(image_features, filenames, styles_df, neighbors, indices)

print(f"Recommendation Accuracy (based on category matching, 10 samples): {accuracy:.2f}%")
print(f"Total valid samples: {total_valid}, Correct: {correct}")