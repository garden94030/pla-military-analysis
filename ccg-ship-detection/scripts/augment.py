#!/usr/bin/env python3
"""
CCG Ship Detection - Data Augmentation Pipeline
中共海警船偵測 - 資料增強管線

Maritime-specific augmentation strategies for ship detection in satellite imagery.
"""

import logging
import random
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_maritime_augmentation_pipeline():
    """
    Create an augmentation pipeline optimized for maritime satellite imagery.

    Key considerations:
    - Ships can appear at any rotation angle
    - Water surface varies with weather/sea state
    - Illumination varies with sun angle and atmospheric conditions
    - Scale varies with satellite altitude and resolution
    """
    try:
        import albumentations as A
    except ImportError:
        logger.error("albumentations required. Install: pip install albumentations")
        return None

    return A.Compose([
        # Geometric transforms
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.RandomRotate90(p=0.5),
        A.Affine(
            rotate=(-15, 15),
            scale=(0.8, 1.2),
            translate_percent={"x": (-0.1, 0.1), "y": (-0.1, 0.1)},
            p=0.3,
        ),

        # Color/radiometric transforms (simulate different conditions)
        A.OneOf([
            A.RandomBrightnessContrast(
                brightness_limit=0.2, contrast_limit=0.2, p=1.0
            ),
            A.CLAHE(clip_limit=4.0, tile_grid_size=(8, 8), p=1.0),
            A.ColorJitter(
                brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05, p=1.0
            ),
        ], p=0.5),

        # Simulate atmospheric effects
        A.OneOf([
            A.GaussianBlur(blur_limit=(3, 5), p=1.0),  # Atmospheric haze
            A.GaussNoise(p=1.0),  # Sensor noise
        ], p=0.2),

        # Simulate partial cloud cover
        A.CoarseDropout(
            num_holes_range=(1, 3),
            hole_height_range=(20, 80),
            hole_width_range=(20, 80),
            fill=255,  # White for clouds
            p=0.1,
        ),

    ], bbox_params=A.BboxParams(
        format="yolo",
        label_fields=["class_labels"],
        min_visibility=0.3,
    ))


def augment_image_and_labels(image_path: Path, label_path: Path,
                              output_images_dir: Path, output_labels_dir: Path,
                              num_augmentations: int = 3):
    """
    Apply augmentation to a single image and its labels.

    Args:
        image_path: Source image
        label_path: Corresponding YOLO label file
        output_images_dir: Directory for augmented images
        output_labels_dir: Directory for augmented labels
        num_augmentations: Number of augmented copies per image
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        logger.error("opencv-python and numpy required.")
        return

    pipeline = get_maritime_augmentation_pipeline()
    if pipeline is None:
        return

    img = cv2.imread(str(image_path))
    if img is None:
        logger.warning(f"Failed to read: {image_path}")
        return

    # Parse YOLO labels
    bboxes = []
    class_labels = []
    if label_path.exists():
        with open(label_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 5:
                    class_labels.append(int(parts[0]))
                    bboxes.append([float(x) for x in parts[1:5]])

    output_images_dir.mkdir(parents=True, exist_ok=True)
    output_labels_dir.mkdir(parents=True, exist_ok=True)

    stem = image_path.stem

    for i in range(num_augmentations):
        try:
            result = pipeline(
                image=img,
                bboxes=bboxes,
                class_labels=class_labels,
            )

            aug_img = result["image"]
            aug_bboxes = result["bboxes"]
            aug_classes = result["class_labels"]

            # Save augmented image
            aug_name = f"{stem}_aug{i:02d}"
            cv2.imwrite(str(output_images_dir / f"{aug_name}.png"), aug_img)

            # Save augmented labels
            with open(output_labels_dir / f"{aug_name}.txt", "w") as f:
                for cls, bbox in zip(aug_classes, aug_bboxes):
                    f.write(f"{cls} {bbox[0]:.6f} {bbox[1]:.6f} "
                            f"{bbox[2]:.6f} {bbox[3]:.6f}\n")

        except Exception as e:
            logger.warning(f"Augmentation {i} failed for {stem}: {e}")


def augment_dataset(images_dir: str, labels_dir: str, num_augmentations: int = 3):
    """Augment all images in a dataset split."""
    images_path = Path(images_dir)
    labels_path = Path(labels_dir)

    image_files = sorted(
        f for f in images_path.iterdir()
        if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif"}
    )

    logger.info(f"Augmenting {len(image_files)} images x{num_augmentations}")

    for img_file in image_files:
        label_file = labels_path / f"{img_file.stem}.txt"
        augment_image_and_labels(
            img_file, label_file,
            images_path, labels_path,
            num_augmentations,
        )

    logger.info("Augmentation complete.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Augment ship detection dataset")
    parser.add_argument("--images", required=True, help="Images directory")
    parser.add_argument("--labels", required=True, help="Labels directory")
    parser.add_argument("--num-aug", type=int, default=3,
                        help="Augmentations per image (default: 3)")
    args = parser.parse_args()

    augment_dataset(args.images, args.labels, args.num_aug)
