#!/usr/bin/env python3
"""
CCG Ship Detection - Annotation Format Converter
中共海警船偵測 - 標註格式轉換

Converts between annotation formats:
- YOLO (normalized xywh) <-> COCO (absolute xywh) <-> Pascal VOC (xyxy)
"""

import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_classes():
    config_path = PROJECT_ROOT / "configs" / "classes.json"
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {cls["id"]: cls["name_en"] for cls in data["classes"]}


def yolo_to_coco(labels_dir: str, images_dir: str, output_path: str,
                 image_width: int = 640, image_height: int = 640):
    """
    Convert YOLO format annotations to COCO JSON format.

    YOLO format: <class_id> <x_center> <y_center> <width> <height> (normalized)
    COCO format: {"x": x, "y": y, "width": w, "height": h} (absolute pixels)
    """
    class_names = load_classes()
    labels_path = Path(labels_dir)
    images_path = Path(images_dir)

    coco = {
        "info": {
            "description": "CCG Ship Detection Dataset",
            "version": "1.0",
            "year": 2026,
        },
        "licenses": [],
        "categories": [],
        "images": [],
        "annotations": [],
    }

    # Categories
    for class_id, name in class_names.items():
        coco["categories"].append({
            "id": class_id,
            "name": name,
            "supercategory": "vessel",
        })

    image_id = 0
    annotation_id = 0

    for label_file in sorted(labels_path.glob("*.txt")):
        image_name = label_file.stem + ".png"
        image_path = images_path / image_name

        # Try other extensions if .png not found
        if not image_path.exists():
            for ext in [".jpg", ".jpeg", ".tif"]:
                alt = images_path / (label_file.stem + ext)
                if alt.exists():
                    image_name = alt.name
                    break

        coco["images"].append({
            "id": image_id,
            "file_name": image_name,
            "width": image_width,
            "height": image_height,
        })

        with open(label_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                class_id = int(parts[0])
                x_center = float(parts[1]) * image_width
                y_center = float(parts[2]) * image_height
                w = float(parts[3]) * image_width
                h = float(parts[4]) * image_height

                x = x_center - w / 2
                y = y_center - h / 2

                coco["annotations"].append({
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": class_id,
                    "bbox": [round(x, 2), round(y, 2), round(w, 2), round(h, 2)],
                    "area": round(w * h, 2),
                    "iscrowd": 0,
                })
                annotation_id += 1

        image_id += 1

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(coco, f, indent=2, ensure_ascii=False)

    logger.info(f"Converted {image_id} images, {annotation_id} annotations -> {output_path}")


def yolo_to_voc(labels_dir: str, images_dir: str, output_dir: str,
                image_width: int = 640, image_height: int = 640):
    """
    Convert YOLO format to Pascal VOC XML format.
    """
    class_names = load_classes()
    labels_path = Path(labels_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    count = 0
    for label_file in sorted(labels_path.glob("*.txt")):
        image_name = label_file.stem + ".png"

        root = ET.Element("annotation")
        ET.SubElement(root, "filename").text = image_name

        size = ET.SubElement(root, "size")
        ET.SubElement(size, "width").text = str(image_width)
        ET.SubElement(size, "height").text = str(image_height)
        ET.SubElement(size, "depth").text = "3"

        with open(label_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                class_id = int(parts[0])
                x_center = float(parts[1]) * image_width
                y_center = float(parts[2]) * image_height
                w = float(parts[3]) * image_width
                h = float(parts[4]) * image_height

                xmin = int(x_center - w / 2)
                ymin = int(y_center - h / 2)
                xmax = int(x_center + w / 2)
                ymax = int(y_center + h / 2)

                obj = ET.SubElement(root, "object")
                ET.SubElement(obj, "name").text = class_names.get(class_id, f"class_{class_id}")
                ET.SubElement(obj, "difficult").text = "0"

                bndbox = ET.SubElement(obj, "bndbox")
                ET.SubElement(bndbox, "xmin").text = str(max(0, xmin))
                ET.SubElement(bndbox, "ymin").text = str(max(0, ymin))
                ET.SubElement(bndbox, "xmax").text = str(min(image_width, xmax))
                ET.SubElement(bndbox, "ymax").text = str(min(image_height, ymax))

        tree = ET.ElementTree(root)
        xml_path = output_path / f"{label_file.stem}.xml"
        tree.write(str(xml_path), encoding="unicode", xml_declaration=True)
        count += 1

    logger.info(f"Converted {count} annotations to VOC format -> {output_dir}")


def coco_to_yolo(coco_json: str, output_dir: str):
    """Convert COCO JSON annotations to YOLO format."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with open(coco_json, "r", encoding="utf-8") as f:
        coco = json.load(f)

    # Build image lookup
    images = {img["id"]: img for img in coco["images"]}

    # Group annotations by image
    annotations_by_image = {}
    for ann in coco["annotations"]:
        img_id = ann["image_id"]
        annotations_by_image.setdefault(img_id, []).append(ann)

    count = 0
    for img_id, img_info in images.items():
        w = img_info["width"]
        h = img_info["height"]
        stem = Path(img_info["file_name"]).stem
        label_path = output_path / f"{stem}.txt"

        anns = annotations_by_image.get(img_id, [])
        with open(label_path, "w") as f:
            for ann in anns:
                bbox = ann["bbox"]  # [x, y, w, h] absolute
                x_center = (bbox[0] + bbox[2] / 2) / w
                y_center = (bbox[1] + bbox[3] / 2) / h
                bw = bbox[2] / w
                bh = bbox[3] / h
                f.write(f"{ann['category_id']} {x_center:.6f} {y_center:.6f} "
                        f"{bw:.6f} {bh:.6f}\n")
        count += 1

    logger.info(f"Converted {count} images from COCO -> YOLO format in {output_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert annotation formats")
    subparsers = parser.add_subparsers(dest="command")

    # YOLO -> COCO
    y2c = subparsers.add_parser("yolo2coco")
    y2c.add_argument("--labels", required=True)
    y2c.add_argument("--images", required=True)
    y2c.add_argument("--output", required=True)
    y2c.add_argument("--width", type=int, default=640)
    y2c.add_argument("--height", type=int, default=640)

    # YOLO -> VOC
    y2v = subparsers.add_parser("yolo2voc")
    y2v.add_argument("--labels", required=True)
    y2v.add_argument("--images", required=True)
    y2v.add_argument("--output", required=True)
    y2v.add_argument("--width", type=int, default=640)
    y2v.add_argument("--height", type=int, default=640)

    # COCO -> YOLO
    c2y = subparsers.add_parser("coco2yolo")
    c2y.add_argument("--coco-json", required=True)
    c2y.add_argument("--output", required=True)

    args = parser.parse_args()

    if args.command == "yolo2coco":
        yolo_to_coco(args.labels, args.images, args.output, args.width, args.height)
    elif args.command == "yolo2voc":
        yolo_to_voc(args.labels, args.images, args.output, args.width, args.height)
    elif args.command == "coco2yolo":
        coco_to_yolo(args.coco_json, args.output)
    else:
        parser.print_help()
