"""
Pet Breed Identification - Model Training Script
=================================================
Uses transfer learning with MobileNetV2 on the Oxford-IIIT Pet Dataset
(37 breed classes: 25 dog + 12 cat breeds).

Usage:
    python ml/train_model.py
"""

import json
import os
import sys

import numpy as np
import tensorflow as tf
import tensorflow_datasets as tfds

# ── Configuration ──────────────────────────────────────────────────────────────
IMG_SIZE        = 224
BATCH_SIZE      = 32
EPOCHS          = 10
LEARNING_RATE   = 1e-3
MODEL_DIR       = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH      = os.path.join(MODEL_DIR, "pet_breed_model.keras")
LABELS_PATH     = os.path.join(MODEL_DIR, "breed_labels.json")


# ── Dataset helpers ────────────────────────────────────────────────────────────
def preprocess(example):
    """Resize, normalise image and one-hot encode label."""
    image = tf.image.resize(example["image"], (IMG_SIZE, IMG_SIZE))
    image = tf.cast(image, tf.float32) / 255.0
    label = example["label"]
    return image, label


def augment(image, label):
    """Simple data augmentation for training."""
    image = tf.image.random_flip_left_right(image)
    image = tf.image.random_brightness(image, 0.2)
    image = tf.image.random_contrast(image, 0.8, 1.2)
    image = tf.clip_by_value(image, 0.0, 1.0)
    return image, label


# ── Build model ────────────────────────────────────────────────────────────────
def build_model(num_classes: int) -> tf.keras.Model:
    """MobileNetV2 transfer-learning model."""
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False  # freeze feature extractor

    model = tf.keras.Sequential([
        base_model,
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(256, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(num_classes, activation="softmax"),
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Pet Breed Identification – Model Training")
    print("=" * 60)

    # 1. Load dataset
    print("\n[1/5] Downloading Oxford-IIIT Pets dataset …")
    (ds_train, ds_test), ds_info = tfds.load(
        "oxford_iiit_pet",
        split=["train", "test"],
        with_info=True,
        as_supervised=False,
    )

    num_classes = ds_info.features["label"].num_classes
    class_names = ds_info.features["label"].names
    print(f"      Found {num_classes} breed classes.")
    print(f"      Train samples: {ds_info.splits['train'].num_examples}")
    print(f"      Test  samples: {ds_info.splits['test'].num_examples}")

    # 2. Preprocess
    print("\n[2/5] Preprocessing images …")
    train_ds = (
        ds_train
        .map(preprocess, num_parallel_calls=tf.data.AUTOTUNE)
        .map(augment,     num_parallel_calls=tf.data.AUTOTUNE)
        .shuffle(1000)
        .batch(BATCH_SIZE)
        .prefetch(tf.data.AUTOTUNE)
    )
    test_ds = (
        ds_test
        .map(preprocess, num_parallel_calls=tf.data.AUTOTUNE)
        .batch(BATCH_SIZE)
        .prefetch(tf.data.AUTOTUNE)
    )

    # 3. Build model
    print("\n[3/5] Building MobileNetV2 model …")
    model = build_model(num_classes)
    model.summary()

    # 4. Train
    print(f"\n[4/5] Training for {EPOCHS} epochs …")
    history = model.fit(
        train_ds,
        validation_data=test_ds,
        epochs=EPOCHS,
        verbose=1,
    )

    # 5. Save
    print("\n[5/5] Saving model & labels …")
    model.save(MODEL_PATH)
    print(f"      Model saved → {MODEL_PATH}")

    # Map label index to (breed_name, species)
    # Oxford-IIIT classes are named like "american_bulldog", "Persian", etc.
    # The dataset has 12 cat breeds and 25 dog breeds.
    CAT_BREEDS = {
        "Abyssinian", "Bengal", "Birman", "Bombay", "British_Shorthair",
        "Egyptian_Mau", "Maine_Coon", "Persian", "Ragdoll", "Russian_Blue",
        "Siamese", "Sphynx",
    }

    labels_info = {}
    for i, name in enumerate(class_names):
        species = "cat" if name in CAT_BREEDS else "dog"
        display_name = name.replace("_", " ").title()
        labels_info[str(i)] = {
            "breed": display_name,
            "species": species,
        }

    with open(LABELS_PATH, "w") as f:
        json.dump(labels_info, f, indent=2)
    print(f"      Labels saved → {LABELS_PATH}")

    # Final accuracy
    val_loss, val_acc = model.evaluate(test_ds, verbose=0)
    print(f"\n✅  Validation accuracy: {val_acc * 100:.1f}%")
    print("    Training complete!")


if __name__ == "__main__":
    main()
