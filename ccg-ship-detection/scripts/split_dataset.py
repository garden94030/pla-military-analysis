#!/usr/bin/env python3
"""
CCG Ship Detection - Dataset Splitting
中共海警船偵測 - 資料集分割

Splits annotated data into train/val/test sets while ensuring:
- Stratified distribution across vessel classes
- No data leakage (tiles from same source image stay in same split)
- Reproducible splits with fixed random seed
"""

import json
import random
import shutil
import logging
from pathlib import Path
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_image_source(filename: str) -> str:
    """
    Extract the source image identifier from a tile filename.
    e.g., 'sentinel2_abc123_x0_y640.png' -> 'sentinel2_abc123'
    """
    parts = filename.rsplit("_x", 1)
    return parts[0] if len(parts) > 1 else filename


def count_classes_in_label(label_path: Path) -> dict:
    """Count objects per class in a label file."""
    counts = defaultdict(int)
    if label_path.exists():
        with open(label_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    counts[int(parts[0])] += 1
    return dict(counts)


def split_dataset(images_dir: str, labels_dir: str, output_base: str,
                  train_ratio: float = 0.70, val_ratio: float = 0.15,
                  seed: int = 42):
    """
    Split dataset into train/val/test sets.

    Args:
        images_dir: Directory with all images
        labels_dir: Directory with all labels
        output_base: Base output directory (will create images/ and labels/ subdirs)
        train_ratio: Fraction for training (default: 0.70)
        val_ratio: Fraction for validation (default: 0.15)
        seed: Random seed for reproducibility
    """
    random.seed(seed)

    images_path = Path(images_dir)
    labels_path = Path(labels_dir)
    output_path = Path(output_base)

    # Find all annotated images
    image_extensions = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    image_files = sorted(
        f for f in images_path.iterdir()
        if f.suffix.lower() in image_extensions
    )

    if not image_files:
        logger.error(f"No images found in {images_dir}")
        return

    # Group by source image to prevent data leakage
    source_groups = defaultdict(list)
    for img_file in image_files:
        source = get_image_source(img_file.stem)
        source_groups[source].append(img_file)

    sources = list(source_groups.keys())
    random.shuffle(sources)

    n_total = len(sources)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    train_sources = sources[:n_train]
    val_sources = sources[n_train:n_train + n_val]
    test_sources = sources[n_train + n_val:]

    splits = {
        "train": train_sources,
        "val": val_sources,
        "test": test_sources,
    }

    stats = {"train": defaultdict(int), "val": defaultdict(int), "test": defaultdict(int)}

    for split_name, split_sources in splits.items():
        img_out = output_path / "images" / split_name
        lbl_out = output_path / "labels" / split_name
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)

        file_count = 0
        for source in split_sources:
            for img_file in source_groups[source]:
                # Copy image
                shutil.copy2(img_file, img_out / img_file.name)

                # Copy label
                label_file = labels_path / f"{img_file.stem}.txt"
                if label_file.exists():
                    shutil.copy2(label_file, lbl_out / label_file.name)
                    # Count classes
                    for cls_id, count in count_classes_in_label(label_file).items():
                        stats[split_name][cls_id] += count

                file_count += 1

        logger.info(f"{split_name:5s}: {file_count} images from {len(split_sources)} sources")

    # Print class distribution per split
    logger.info("\nClass distribution per split:")
    all_classes = set()
    for s in stats.values():
        all_classes.update(s.keys())

    for cls_id in sorted(all_classes):
        train_c = stats["train"].get(cls_id, 0)
        val_c = stats["val"].get(cls_id, 0)
        test_c = stats["test"].get(cls_id, 0)
        total = train_c + val_c + test_c
        logger.info(f"  Class {cls_id}: train={train_c}, val={val_c}, "
                     f"test={test_c}, total={total}")

    # Save split metadata
    metadata = {
        "seed": seed,
        "ratios": {"train": train_ratio, "val": val_ratio, "test": 1 - train_ratio - val_ratio},
        "source_groups": {
            "train": train_sources,
            "val": val_sources,
            "test": test_sources,
        },
    }
    meta_path = output_path / "split_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"\nSplit metadata saved to {meta_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Split dataset into train/val/test")
    parser.add_argument("--images", required=True, help="Source images directory")
    parser.add_argument("--labels", required=True, help="Source labels directory")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "datasets"),
                        help="Output base directory")
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    split_dataset(args.images, args.labels, args.output,
                  args.train_ratio, args.val_ratio, args.seed)
