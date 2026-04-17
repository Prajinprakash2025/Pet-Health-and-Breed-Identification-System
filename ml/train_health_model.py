import json
import os
from pathlib import Path
from typing import Dict

import tensorflow as tf
from tensorflow.keras.applications.efficientnet import preprocess_input

# ── Configuration ──────────────────────────────────────────────────────────────
IMG_SIZE        = 224
BATCH_SIZE      = 16
EPOCHS_HEAD     = 10
EPOCHS_FINETUNE = 15

BASE_DIR        = Path(__file__).resolve().parent.parent
DATASETS_DIR    = BASE_DIR / "ml_datasets" / "health_data"
MODEL_DIR       = BASE_DIR / "ml"
MODEL_PATH      = MODEL_DIR / "pet_health_model.keras"
LABELS_PATH     = MODEL_DIR / "health_labels.json"


def build_model(num_classes: int) -> tuple[tf.keras.Model, tf.keras.Model]:
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
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model, base_model


def main():
    print("=" * 60)
    print("  Pet Health Identification – EfficientNetB0 Training")
    print("=" * 60)

    if not DATASETS_DIR.exists():
        raise FileNotFoundError(f"Dataset directory not found: {DATASETS_DIR}")

    # 1. Data augmentation + EfficientNet preprocessing
    print("\n[1/5] Building data pipelines (Train/Val split) …")
    datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rotation_range=20,
        width_shift_range=0.1,
        height_shift_range=0.1,
        zoom_range=0.1,
        horizontal_flip=True,
        validation_split=0.2,
    )

    train_gen = datagen.flow_from_directory(
        str(DATASETS_DIR),
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="training",
        shuffle=True,
        seed=42,
    )

    val_gen = datagen.flow_from_directory(
        str(DATASETS_DIR),
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
        seed=42,
    )

    class_indices = train_gen.class_indices
    sorted_by_index = sorted(class_indices.items(), key=lambda kv: kv[1])
    class_names = [name for name, _ in sorted_by_index]
    num_classes = len(class_names)
    
    print(f"\n      Found Classes: {class_names}")

    # 2. Build model
    print("\n[2/5] Building EfficientNetB0 model …")
    model, base_model = build_model(num_classes)

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=4, restore_best_weights=True, verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=2, min_lr=1e-7, verbose=1
        ),
    ]

    # 3. Stage 1 – train head
    print(f"\n[3/5] Stage 1: Training classifier head ({EPOCHS_HEAD} epochs) …")
    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_HEAD,
        callbacks=callbacks,
        verbose=1,
    )

    # 4. Stage 2 – fine-tune
    print(f"\n[4/5] Stage 2: Fine-tuning top 30 layers ({EPOCHS_FINETUNE} epochs) …")
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-4),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    history_ft = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_FINETUNE,
        callbacks=callbacks,
        verbose=1,
    )

    # 5. Save model and labels
    print("\n[5/5] Saving model & labels …")
    model.save(MODEL_PATH)
    
    # Save label mapping compatible with ml_predictor logic
    label_map = {}
    for idx, name in enumerate(class_names):
        label_map[str(idx)] = {
            "disease": name,
            "description": name.replace("_", " ").title()
        }

    with open(LABELS_PATH, "w", encoding="utf-8") as f:
        json.dump(label_map, f, indent=2)

    val_loss, val_acc = model.evaluate(val_gen, verbose=0)
    print(f"\n✅ Final validation accuracy: {val_acc * 100:.1f}%")
    print(f"   Model saved to {MODEL_PATH}")
    print(f"   Labels saved to {LABELS_PATH}")

if __name__ == "__main__":
    main()
