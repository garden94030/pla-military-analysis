#!/usr/bin/env python3
"""
CCG Ship Detection - Dataset Validation
中共海警船偵測 - 資料集驗證

Validates dataset integrity:
- Image-label pairing consistency
- Annotation format correctness
- Bounding box validity
- Class distribution balance
- Duplicate detection
"""

import hashlib
import json
import logging
import sys
from pathlib import Path
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_classes():
    config_path = PROJECT_ROOT / "configs" / "classes.json"
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {cls["id"] for cls in data["classes"]}


def validate_yolo_label(label_path: Path, valid_classes: set) -> list:
    """Validate a single YOLO label file. Returns list of error strings."""
    errors = []
    with open(label_path, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) != 5:
                errors.append(
                    f"{label_path.name}:{line_num} - Expected 5 values, got {len(parts)}"
                )
                continue

            try:
                class_id = int(parts[0])
                x, y, w, h = [float(v) for v in parts[1:5]]
            except ValueError:
                errors.append(f"{label_path.name}:{line_num} - Invalid numeric values")
                continue

            if class_id not in valid_classes:
                errors.append(
                    f"{label_path.name}:{line_num} - Unknown class {class_id}"
                )

            for name, val in [("x", x), ("y", y), ("w", w), ("h", h)]:
                if not (0.0 <= val <= 1.0):
                    errors.append(
                        f"{label_path.name}:{line_num} - {name}={val} out of [0,1] range"
                    )

            if w <= 0 or h <= 0:
                errors.append(
                    f"{label_path.name}:{line_num} - Invalid box size w={w}, h={h}"
                )

    return errors


def file_hash(path: Path) -> str:
    """Compute MD5 hash of a file for duplicate detection."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_dataset(dataset_dir: str) -> bool:
    """
    Run all validation checks on the dataset.

    Returns True if no critical errors found.
    """
    dataset_path = Path(dataset_dir)
    valid_classes = load_classes()
    image_extensions = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}

    all_errors = []
    all_warnings = []
    total_images = 0
    total_labels = 0
    total_objects = 0
    class_counts = defaultdict(int)

    for split in ["train", "val", "test"]:
        images_dir = dataset_path / "images" / split
        labels_dir = dataset_path / "labels" / split

        if not images_dir.exists():
            all_warnings.append(f"Missing images directory: {images_dir}")
            continue

        images = {
            f.stem: f for f in images_dir.iterdir()
            if f.suffix.lower() in image_extensions
        }
        labels = {
            f.stem: f for f in labels_dir.iterdir()
            if f.suffix == ".txt"
        } if labels_dir.exists() else {}

        total_images += len(images)
        total_labels += len(labels)

        # Check for images without labels
        missing_labels = set(images.keys()) - set(labels.keys())
        if missing_labels:
            all_warnings.append(
                f"[{split}] {len(missing_labels)} images without labels: "
                f"{list(missing_labels)[:5]}..."
            )

        # Check for labels without images
        orphan_labels = set(labels.keys()) - set(images.keys())
        if orphan_labels:
            all_errors.append(
                f"[{split}] {len(orphan_labels)} labels without images: "
                f"{list(orphan_labels)[:5]}..."
            )

        # Validate each label file
        for stem, label_path in labels.items():
            errors = validate_yolo_label(label_path, valid_classes)
            all_errors.extend(errors)

            # Count objects
            with open(label_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 5:
                        total_objects += 1
                        class_counts[int(parts[0])] += 1

        # Check for duplicate images
        hashes = defaultdict(list)
        for img_path in images.values():
            h = file_hash(img_path)
            hashes[h].append(img_path.name)

        for h, files in hashes.items():
            if len(files) > 1:
                all_warnings.append(
                    f"[{split}] Duplicate images: {files}"
                )

    # Print validation report
    logger.info("\n" + "=" * 60)
    logger.info("CCG Ship Detection - Dataset Validation Report")
    logger.info("=" * 60)
    logger.info(f"\nTotal images: {total_images}")
    logger.info(f"Total labels: {total_labels}")
    logger.info(f"Total objects: {total_objects}")

    logger.info("\nClass Distribution:")
    for cls_id in sorted(class_counts.keys()):
        count = class_counts[cls_id]
        pct = count / total_objects * 100 if total_objects > 0 else 0
        logger.info(f"  Class {cls_id}: {count:5d} ({pct:.1f}%)")

    if all_warnings:
        logger.warning(f"\nWarnings ({len(all_warnings)}):")
        for w in all_warnings:
            logger.warning(f"  - {w}")

    if all_errors:
        logger.error(f"\nErrors ({len(all_errors)}):")
        for e in all_errors[:20]:
            logger.error(f"  - {e}")
        if len(all_errors) > 20:
            logger.error(f"  ... and {len(all_errors) - 20} more errors")
        logger.info("\nValidation: FAILED")
        return False

    logger.info("\nValidation: PASSED")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate ship detection dataset")
    parser.add_argument("--dataset", default=str(PROJECT_ROOT / "datasets"),
                        help="Dataset root directory")
    args = parser.parse_args()

    success = validate_dataset(args.dataset)
    sys.exit(0 if success else 1)
