import pickle as pkl
features = pkl.load(open("Backend/Images_features.pkl", "rb"))
filenames = pkl.load(open("Backend/filenames.pkl", "rb"))
print(f"Loaded {len(features)} features and {len(filenames)} filenames")