"""
ML Predictor – Pet Breed & Health Identification
================================================
Loads the trained EfficientNetB0 models and provides
predict_breed(image_path) and predict_health(image_path)
for use in Django views.
"""

import json
import os

import numpy as np
from PIL import Image

_breed_model = None
_breed_labels = None
_health_model = None
_health_labels = None

IMG_SIZE   = 224
ML_DIR     = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml")
BREED_MODEL_PATH = os.path.join(ML_DIR, "pet_breed_model.keras")
BREED_LABELS_PATH = os.path.join(ML_DIR, "breed_labels.json")
HEALTH_MODEL_PATH = os.path.join(ML_DIR, "pet_health_model.keras")
HEALTH_LABELS_PATH = os.path.join(ML_DIR, "health_labels.json")


def _load_breed_model():
    global _breed_model, _breed_labels
    if _breed_model is None:
        import tensorflow as tf
        _breed_model = tf.keras.models.load_model(BREED_MODEL_PATH, compile=False)
    if _breed_labels is None:
        with open(BREED_LABELS_PATH) as f:
            _breed_labels = json.load(f)
    return _breed_model, _breed_labels

def _load_health_model():
    global _health_model, _health_labels
    if _health_model is None:
        import tensorflow as tf
        _health_model = tf.keras.models.load_model(HEALTH_MODEL_PATH, compile=False)
    if _health_labels is None:
        with open(HEALTH_LABELS_PATH) as f:
            _health_labels = json.load(f)
    return _health_model, _health_labels


def _preprocess_image(image_path: str) -> np.ndarray:
    # EfficientNet expects raw [0,255] pixels — no manual scaling needed
    img = Image.open(image_path).convert("RGB")
    img = img.resize((IMG_SIZE, IMG_SIZE))
    img_array = np.array(img, dtype=np.float32)
    return np.expand_dims(img_array, axis=0)


def predict_breed(image_path: str) -> dict:
    """Returns dict with top predicted breed details."""
    model, labels = _load_breed_model()
    img_array = _preprocess_image(image_path)
    predictions = model.predict(img_array, verbose=0)[0]

    best_idx  = int(predictions.argsort()[-1])
    best_info = labels[str(best_idx)]
    best_conf = float(predictions[best_idx])

    return {
        "breed": best_info["breed"],
        "species": best_info["species"],
        "confidence": round(best_conf * 100, 2),
        "low_confidence": best_conf < 0.45,
    }


def predict_health(image_path: str) -> dict:
    """Returns dict with predicted health conditions."""
    model, labels = _load_health_model()
    img_array = _preprocess_image(image_path)
    predictions = model.predict(img_array, verbose=0)[0]

    best_idx = int(predictions.argsort()[-1])
    best_info = labels[str(best_idx)]
    best_conf = float(predictions[best_idx])
    
    return {
        "disease": best_info["disease"],
        "description": best_info["description"],
        "confidence": round(best_conf * 100, 2),
        "low_confidence": best_conf < 0.50,
    }

