#!/usr/bin/env python3
"""
CCG Ship Detection - Annotation Helper
中共海警船偵測 - 標註輔助工具

Provides utilities for annotating ship detection datasets:
- Launch labelImg/CVAT for manual annotation
- Semi-automatic annotation using pre-trained models
- Annotation verification and statistics
"""

import json
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_classes(config_path: str = None) -> dict:
    """Load class definitions from config."""
    if config_path is None:
        config_path = str(PROJECT_ROOT / "configs" / "classes.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_labelimg_classes(output_path: str = None):
    """Generate predefined_classes.txt for labelImg tool."""
    if output_path is None:
        output_path = str(PROJECT_ROOT / "configs" / "predefined_classes.txt")

    classes = load_classes()
    with open(output_path, "w", encoding="utf-8") as f:
        for cls in classes["classes"]:
            f.write(f"{cls['name_en']}\n")

    logger.info(f"Generated labelImg classes file: {output_path}")


def create_annotation_template(image_path: Path, label_dir: Path):
    """Create an empty YOLO annotation file for an image."""
    label_dir.mkdir(parents=True, exist_ok=True)
    label_path = label_dir / f"{image_path.stem}.txt"
    if not label_path.exists():
        label_path.touch()
    return label_path


def setup_annotation_workspace(images_dir: str):
    """
    Set up annotation workspace:
    - Create label directories
    - Generate empty annotation files
    - Generate class definition files
    """
    images_path = Path(images_dir)
    if not images_path.exists():
        logger.error(f"Images directory not found: {images_dir}")
        return

    # Determine corresponding label directory
    label_dir = images_path.parent.parent / "labels" / images_path.name
    label_dir.mkdir(parents=True, exist_ok=True)

    # Create empty annotations for all images
    image_extensions = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    count = 0
    for img_file in images_path.iterdir():
        if img_file.suffix.lower() in image_extensions:
            create_annotation_template(img_file, label_dir)
            count += 1

    logger.info(f"Created {count} annotation templates in {label_dir}")

    # Generate class files
    generate_labelimg_classes()

    logger.info(
        "\nAnnotation workspace ready!"
        "\n\nTo start annotating with labelImg:"
        f"\n  labelImg {images_dir} "
        f"{PROJECT_ROOT / 'configs' / 'predefined_classes.txt'} {label_dir}"
        "\n\nOr use CVAT for collaborative annotation:"
        "\n  https://cvat.org"
    )


def compute_annotation_stats(labels_dir: str):
    """Compute statistics on existing annotations."""
    labels_path = Path(labels_dir)
    if not labels_path.exists():
        logger.error(f"Labels directory not found: {labels_dir}")
        return

    classes = load_classes()
    class_names = {cls["id"]: cls["name_en"] for cls in classes["classes"]}

    stats = {
        "total_images": 0,
        "annotated_images": 0,
        "empty_images": 0,
        "total_objects": 0,
        "class_counts": {cls["id"]: 0 for cls in classes["classes"]},
    }

    for label_file in labels_path.glob("*.txt"):
        stats["total_images"] += 1
        with open(label_file, "r") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        if lines:
            stats["annotated_images"] += 1
            stats["total_objects"] += len(lines)
            for line in lines:
                parts = line.split()
                if parts:
                    class_id = int(parts[0])
                    stats["class_counts"][class_id] = (
                        stats["class_counts"].get(class_id, 0) + 1
                    )
        else:
            stats["empty_images"] += 1

    # Print report
    logger.info("\n=== Annotation Statistics ===")
    logger.info(f"Total images:     {stats['total_images']}")
    logger.info(f"Annotated images: {stats['annotated_images']}")
    logger.info(f"Empty images:     {stats['empty_images']}")
    logger.info(f"Total objects:    {stats['total_objects']}")
    logger.info("\nClass Distribution:")
    for class_id, count in stats["class_counts"].items():
        name = class_names.get(class_id, f"Unknown({class_id})")
        pct = (count / stats["total_objects"] * 100) if stats["total_objects"] > 0 else 0
        logger.info(f"  [{class_id}] {name:25s}: {count:5d} ({pct:.1f}%)")

    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Annotation helper for CCG ship detection")
    subparsers = parser.add_subparsers(dest="command")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up annotation workspace")
    setup_parser.add_argument("--images", required=True, help="Path to images directory")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Compute annotation statistics")
    stats_parser.add_argument("--labels", required=True, help="Path to labels directory")

    args = parser.parse_args()

    if args.command == "setup":
        setup_annotation_workspace(args.images)
    elif args.command == "stats":
        compute_annotation_stats(args.labels)
    else:
        parser.print_help()
