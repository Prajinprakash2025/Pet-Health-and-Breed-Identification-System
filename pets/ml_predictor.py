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
MODEL_PATH = os.path.join(ML_DIR, "model", "dog_breed_model.h5")
LABELS_PATH = os.path.join(ML_DIR, "breed_labels.json")


def _load_model():
    """Load the Keras model and label map once."""
    global _model, _labels

    if _model is None:
        import tensorflow as tf
        _model = tf.keras.models.load_model(MODEL_PATH, compile=False)

    if _labels is None:
        with open(LABELS_PATH) as f:
            _labels = json.load(f)

    return _model, _labels


def _preprocess_image(image_path: str) -> np.ndarray:
    """Load an image from disk and preprocess it for MobileNetV2."""
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

    img = Image.open(image_path).convert("RGB")
    img = img.resize((IMG_SIZE, IMG_SIZE))
    img_array = np.array(img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)  # add batch dimension
    img_array = preprocess_input(img_array)
    return img_array


def predict_breed(image_path: str) -> dict:
    """
    Run breed prediction on a pet image.

    Returns
    -------
    dict with keys:
        breed          – human-readable breed name or "Low confidence prediction"
        species        – "dog" or "cat"
        confidence     – float 0-100 for the best prediction
        top3           – list of {breed, species, confidence}
        low_confidence – bool flag indicating if confidence < 60%
    """
    model, labels = _load_model()
    img_array = _preprocess_image(image_path)

    # Predict
    predictions = model.predict(img_array, verbose=0)[0]

    # Top-3 predictions
    top3_indices = predictions.argsort()[-3:][::-1]
    top3 = []
    for idx in top3_indices:
        info = labels[str(idx)]
        conf = float(predictions[idx])
        top3.append(
            {
                "breed": info["breed"],
                "species": info["species"],
                "confidence": round(conf * 100, 2),
            }
        )

    best_idx = int(top3_indices[0])
    best_info = labels[str(best_idx)]
    best_conf = float(predictions[best_idx])
    low_conf = best_conf < 0.6

    breed_name = "Low confidence prediction" if low_conf else best_info["breed"]

    return {
        "breed": breed_name,
        "species": best_info["species"],
        "confidence": round(best_conf * 100, 2),
        "top3": top3,
        "low_confidence": low_conf,
    }
