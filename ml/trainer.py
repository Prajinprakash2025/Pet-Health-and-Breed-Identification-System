import json
from pathlib import Path
from typing import Dict, List

import tensorflow as tf
from tensorflow.keras.applications.efficientnet import preprocess_input
from tensorflow.keras.preprocessing.image import ImageDataGenerator


BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "ml_datasets"
MODELS_DIR = BASE_DIR / "ml"
MODEL_PATH = MODELS_DIR / "pet_breed_model.keras"
LABELS_PATH = MODELS_DIR / "breed_labels.json"

IMG_SIZE = 224
BATCH_SIZE = 16


def _build_mobilenet_model(num_classes: int) -> tf.keras.Model:
    """
    Build a transfer-learning model using MobileNetV2 as the feature extractor
    and a custom classifier head.
    """
    base_model = tf.keras.applications.EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
    )
    base_model.trainable = False

    inputs = tf.keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
    x = base_model(inputs, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dense(512, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.4)(x)
    x = tf.keras.layers.Dense(256, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model, base_model


def _build_label_map(class_names: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Build the label map used by ``ml_predictor`` (index -> {breed, species}).

    For this project we focus on dog breeds, so species is always "dog"
    unless the class name clearly indicates a cat.
    """
    label_map: Dict[str, Dict[str, str]] = {}
    for idx, name in enumerate(class_names):
        lower = name.lower()
        species = "cat" if "cat" in lower else "dog"
        label_map[str(idx)] = {"breed": name, "species": species}
    return label_map


def train_from_directory(dataset_root: Path, epochs_head: int = 5, epochs_finetune: int = 5) -> Dict[str, float]:
    """
    Train a MobileNetV2-based classifier on an image dataset organised as:

    dataset_root/
        golden_retriever/
        labrador/
        german_shepherd/
        ...

    Uses an 80/20 train/validation split and two-stage training:
      1) Train only the classifier head (base frozen)
      2) Unfreeze the last 20 layers of MobileNetV2 and fine-tune
    """
    DATASETS_DIR.mkdir(exist_ok=True, parents=True)
    MODELS_DIR.mkdir(exist_ok=True, parents=True)

    dataset_root = Path(dataset_root)
    if not dataset_root.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_root}")

    # Data augmentation + MobileNetV2 preprocessing
    datagen = ImageDataGenerator(
        rotation_range=20,
        width_shift_range=0.1,
        height_shift_range=0.1,
        zoom_range=0.1,
        horizontal_flip=True,
        validation_split=0.2,
        preprocessing_function=preprocess_input,
    )

    train_gen = datagen.flow_from_directory(
        str(dataset_root),
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="training",
        shuffle=True,
        seed=42,
    )

    val_gen = datagen.flow_from_directory(
        str(dataset_root),
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
        seed=42,
    )

    class_indices = train_gen.class_indices  # dict: class_name -> index
    # Ensure class names are ordered by index
    sorted_by_index = sorted(class_indices.items(), key=lambda kv: kv[1])
    class_names = [name for name, _ in sorted_by_index]
    num_classes = len(class_names)

    model, base_model = _build_mobilenet_model(num_classes)

    # Stage 1: train classifier head
    history_head = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=epochs_head,
        verbose=1,
    )

    # Stage 2: fine-tune last 30 layers of base model
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    history_ft = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=epochs_finetune,
        verbose=1,
    )

    # Save trained model
    model.save(MODEL_PATH)

    # Save label mapping compatible with ml_predictor
    label_map = _build_label_map(class_names)
    with open(LABELS_PATH, "w", encoding="utf-8") as f:
        json.dump(label_map, f, indent=2)

    final_train_acc = float(history_ft.history["accuracy"][-1])
    final_val_acc = float(history_ft.history["val_accuracy"][-1])

    return {
        "train_accuracy": final_train_acc,
        "val_accuracy": final_val_acc,
        "num_classes": num_classes,
    }

