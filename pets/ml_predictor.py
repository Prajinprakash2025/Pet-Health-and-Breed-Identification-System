"""
ML Predictor – Pet Breed Identification
========================================
Loads the trained MobileNetV2 model and provides a simple
``predict_breed(image_path)`` function for use in Django views.
"""

import json
import os

import numpy as np
from PIL import Image

# Lazy-loaded globals (singleton pattern)
_model = None
_labels = None

IMG_SIZE = 224
ML_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml")
MODEL_PATH = os.path.join(ML_DIR, "pet_breed_model.keras")
LABELS_PATH = os.path.join(ML_DIR, "breed_labels.json")


def _load_model():
    """Load the Keras model and label map once."""
    global _model, _labels

    if _model is None:
        import tensorflow as tf
        _model = tf.keras.models.load_model(MODEL_PATH)

    if _labels is None:
        with open(LABELS_PATH) as f:
            _labels = json.load(f)

    return _model, _labels


def predict_breed(image_path: str) -> dict:
    """
    Run breed prediction on a pet image.

    Returns
    -------
    dict with keys:
        breed      – human-readable breed name
        species    – "dog" or "cat"
        confidence – float 0-100
        top3       – list of (breed, species, confidence) tuples
    """
    model, labels = _load_model()

    # Load and preprocess the image
    img = Image.open(image_path).convert("RGB")
    img = img.resize((IMG_SIZE, IMG_SIZE))
    img_array = np.array(img, dtype=np.float32) / 255.0
    img_array = np.expand_dims(img_array, axis=0)  # batch dim

    # Predict
    predictions = model.predict(img_array, verbose=0)[0]

    # Top-3 predictions
    top3_indices = predictions.argsort()[-3:][::-1]
    top3 = []
    for idx in top3_indices:
        info = labels[str(idx)]
        top3.append({
            "breed": info["breed"],
            "species": info["species"],
            "confidence": round(float(predictions[idx]) * 100, 2),
        })

    best = top3[0]
    return {
        "breed": best["breed"],
        "species": best["species"],
        "confidence": best["confidence"],
        "top3": top3,
    }
