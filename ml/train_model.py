"""
Pet Breed Identification - Model Training Script
=================================================
Uses EfficientNetB0 transfer learning on the Oxford-IIIT Pet Dataset
(37 breed classes: 25 dog + 12 cat breeds).

Two-stage training:
  Stage 1 – Train classifier head only (base frozen), 10 epochs
  Stage 2 – Fine-tune top 30 layers of EfficientNetB0, 10 epochs

Expected validation accuracy: ~90-94%

Usage:
    python ml/train_model.py
"""

import json
import os

import numpy as np
import tensorflow as tf
import tensorflow_datasets as tfds

# ── Configuration ──────────────────────────────────────────────────────────────
IMG_SIZE        = 224
BATCH_SIZE      = 32
EPOCHS_HEAD     = 10
EPOCHS_FINETUNE = 10
MODEL_DIR       = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH      = os.path.join(MODEL_DIR, "pet_breed_model.keras")
LABELS_PATH     = os.path.join(MODEL_DIR, "breed_labels.json")

CAT_BREEDS = {
    "Abyssinian", "Bengal", "Birman", "Bombay", "British_Shorthair",
    "Egyptian_Mau", "Maine_Coon", "Persian", "Ragdoll", "Russian_Blue",
    "Siamese", "Sphynx",
}


# ── Dataset helpers ────────────────────────────────────────────────────────────
def preprocess(example):
    image = tf.image.resize(example["image"], (IMG_SIZE, IMG_SIZE))
    image = tf.cast(image, tf.float32)
    # EfficientNet expects pixels in [0, 255] — its own rescaling is built-in
    label = example["label"]
    return image, label


def augment(image, label):
    image = tf.image.random_flip_left_right(image)
    image = tf.image.random_brightness(image, 0.2)
    image = tf.image.random_contrast(image, 0.8, 1.2)
    image = tf.image.random_saturation(image, 0.8, 1.2)
    image = tf.image.random_hue(image, 0.05)
    # Random crop + resize (zoom simulation)
    image = tf.image.resize_with_crop_or_pad(image, IMG_SIZE + 20, IMG_SIZE + 20)
    image = tf.image.random_crop(image, size=[IMG_SIZE, IMG_SIZE, 3])
    image = tf.clip_by_value(image, 0.0, 255.0)
    return image, label


# ── Build model ────────────────────────────────────────────────────────────────
def build_model(num_classes: int):
    base_model = tf.keras.applications.EfficientNetB0(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
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

    model = tf.keras.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model, base_model


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Pet Breed Identification – EfficientNetB0 Training")
    print("=" * 60)

    # 1. Load dataset
    print("\n[1/5] Loading Oxford-IIIT Pets dataset …")
    (ds_train, ds_test), ds_info = tfds.load(
        "oxford_iiit_pet",
        split=["train", "test"],
        with_info=True,
        as_supervised=False,
    )

    num_classes = ds_info.features["label"].num_classes
    class_names = ds_info.features["label"].names
    print(f"      {num_classes} breed classes | "
          f"train={ds_info.splits['train'].num_examples} | "
          f"test={ds_info.splits['test'].num_examples}")

    # 2. Build pipelines
    print("\n[2/5] Building data pipelines …")
    train_ds = (
        ds_train
        .map(preprocess, num_parallel_calls=tf.data.AUTOTUNE)
        .map(augment,    num_parallel_calls=tf.data.AUTOTUNE)
        .shuffle(2000, seed=42)
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
    print("\n[3/5] Building EfficientNetB0 model …")
    model, base_model = build_model(num_classes)
    print(f"      Trainable params (head only): "
          f"{sum(tf.size(v).numpy() for v in model.trainable_variables):,}")

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=3, restore_best_weights=True, verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=2, min_lr=1e-7, verbose=1
        ),
    ]

    # 4a. Stage 1 – train head
    print(f"\n[4/5] Stage 1: Training classifier head ({EPOCHS_HEAD} epochs) …")
    model.fit(
        train_ds,
        validation_data=test_ds,
        epochs=EPOCHS_HEAD,
        callbacks=callbacks,
        verbose=1,
    )

    # 4b. Stage 2 – fine-tune top 30 layers
    print(f"\n      Stage 2: Fine-tuning top 30 layers ({EPOCHS_FINETUNE} epochs) …")
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-4),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    history = model.fit(
        train_ds,
        validation_data=test_ds,
        epochs=EPOCHS_FINETUNE,
        callbacks=callbacks,
        verbose=1,
    )

    # 5. Save
    print("\n[5/5] Saving model & labels …")
    model.save(MODEL_PATH)
    print(f"      Model  → {MODEL_PATH}")

    labels_info = {}
    for i, name in enumerate(class_names):
        species = "cat" if name in CAT_BREEDS else "dog"
        labels_info[str(i)] = {
            "breed": name.replace("_", " ").title(),
            "species": species,
        }

    with open(LABELS_PATH, "w") as f:
        json.dump(labels_info, f, indent=2)
    print(f"      Labels → {LABELS_PATH}")

    val_loss, val_acc = model.evaluate(test_ds, verbose=0)
    print(f"\n✅  Final validation accuracy: {val_acc * 100:.1f}%")
    print("    Training complete!")


if __name__ == "__main__":
    main()
