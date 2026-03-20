import os
import zipfile
import shutil

# Create directory structure
base_dir = "dummy_dataset"
nested_dir = os.path.join(base_dir, "dataset_v1")
dog_dir = os.path.join(nested_dir, "dog_breed_1")
cat_dir = os.path.join(nested_dir, "cat_breed_1")

os.makedirs(dog_dir, exist_ok=True)
os.makedirs(cat_dir, exist_ok=True)

# Create dummy image files
with open(os.path.join(dog_dir, "img1.jpg"), "wb") as f:
    f.write(b"dummy image data")
with open(os.path.join(dog_dir, "img2.jpg"), "wb") as f:
    f.write(b"dummy image data")
with open(os.path.join(cat_dir, "img1.jpg"), "wb") as f:
    f.write(b"dummy image data")

# Create a Kaggle-style ZIP with a single top-level folder
zip_path = "test_kaggle_dataset.zip"
with zipfile.ZipFile(zip_path, "w") as zf:
    zf.write(os.path.join(dog_dir, "img1.jpg"), "dataset_v1/dog_breed_1/img1.jpg")
    zf.write(os.path.join(dog_dir, "img2.jpg"), "dataset_v1/dog_breed_1/img2.jpg")
    zf.write(os.path.join(cat_dir, "img1.jpg"), "dataset_v1/cat_breed_1/img1.jpg")

print(f"Created {zip_path}")

# Delete the temporary folders
shutil.rmtree(base_dir)
