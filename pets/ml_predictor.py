"""
ML Predictor – Pet Breed Identification
========================================
Loads the trained EfficientNetB0 model and provides
predict_breed(image_path) for use in Django views.
"""

import json
import os

import numpy as np
from PIL import Image

_model = None
_labels = None

IMG_SIZE   = 224
ML_DIR     = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml")
MODEL_PATH = os.path.join(ML_DIR, "pet_breed_model.keras")
LABELS_PATH = os.path.join(ML_DIR, "breed_labels.json")


def _load_model():
    global _model, _labels
    if _model is None:
        import tensorflow as tf
        _model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    if _labels is None:
        with open(LABELS_PATH) as f:
            _labels = json.load(f)
    return _model, _labels


def _preprocess_image(image_path: str) -> np.ndarray:
    # EfficientNet expects raw [0,255] pixels — no manual scaling needed
    img = Image.open(image_path).convert("RGB")
    img = img.resize((IMG_SIZE, IMG_SIZE))
    img_array = np.array(img, dtype=np.float32)
    return np.expand_dims(img_array, axis=0)


def predict_breed(image_path: str) -> dict:
    """
    Returns dict with keys:
        breed          – best breed name (always shown, even if low confidence)
        species        – "dog" or "cat"
        confidence     – float 0-100
        top3           – list of {breed, species, confidence}
        low_confidence – True if confidence < 45%
    """
    model, labels = _load_model()
    img_array = _preprocess_image(image_path)
    predictions = model.predict(img_array, verbose=0)[0]

    top3_indices = predictions.argsort()[-3:][::-1]
    top3 = []
    for idx in top3_indices:
        info = labels[str(idx)]
        conf = float(predictions[idx])
        top3.append({
            "breed": info["breed"],
            "species": info["species"],
            "confidence": round(conf * 100, 2),
        })

    best_idx  = int(top3_indices[0])
    best_info = labels[str(best_idx)]
    best_conf = float(predictions[best_idx])
    low_conf  = best_conf < 0.45

    return {
        "breed": best_info["breed"],          # always return the breed name
        "species": best_info["species"],
        "confidence": round(best_conf * 100, 2),
        "top3": top3,
        "low_confidence": low_conf,
    }
