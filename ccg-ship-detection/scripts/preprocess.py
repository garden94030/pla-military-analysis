#!/usr/bin/env python3
"""
CCG Ship Detection - Image Preprocessing & Tiling
中共海警船偵測 - 影像前處理與切割

Preprocesses raw satellite imagery:
- Radiometric correction
- Pan-sharpening (if applicable)
- Tiling into detection-ready patches
- Contrast enhancement for maritime scenes
"""

import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def normalize_image(image_array, percentile_low=2, percentile_high=98):
    """
    Percentile-based normalization for satellite imagery.
    Handles varying radiometric conditions across different acquisitions.
    """
    try:
        import numpy as np
    except ImportError:
        logger.error("numpy is required. Install with: pip install numpy")
        return image_array

    low = np.percentile(image_array, percentile_low)
    high = np.percentile(image_array, percentile_high)

    if high - low == 0:
        return np.zeros_like(image_array, dtype=np.uint8)

    normalized = np.clip((image_array - low) / (high - low) * 255, 0, 255)
    return normalized.astype(np.uint8)


def enhance_maritime_contrast(image_array):
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    optimized for maritime scenes where ships appear as bright objects
    against dark water.
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        logger.error("opencv-python is required. Install with: pip install opencv-python")
        return image_array

    if len(image_array.shape) == 3:
        lab = cv2.cvtColor(image_array, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(l_channel)
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    else:
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        return clahe.apply(image_array)


def tile_image(image_path: Path, output_dir: Path, tile_size: int = 640,
               overlap: int = 64, min_ship_area_ratio: float = 0.0):
    """
    Split a large satellite image into tiles suitable for object detection.

    Args:
        image_path: Path to input image
        output_dir: Directory to save tiles
        tile_size: Size of each tile (pixels)
        overlap: Overlap between adjacent tiles (pixels)
        min_ship_area_ratio: Skip tiles with less than this ratio of non-water pixels
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        logger.error("opencv-python and numpy required.")
        return []

    img = cv2.imread(str(image_path))
    if img is None:
        logger.error(f"Failed to read image: {image_path}")
        return []

    h, w = img.shape[:2]
    output_dir.mkdir(parents=True, exist_ok=True)
    tiles = []
    step = tile_size - overlap
    stem = image_path.stem

    for y in range(0, h, step):
        for x in range(0, w, step):
            # Extract tile
            y_end = min(y + tile_size, h)
            x_end = min(x + tile_size, w)
            tile = img[y:y_end, x:x_end]

            # Pad if necessary
            if tile.shape[0] < tile_size or tile.shape[1] < tile_size:
                padded = np.zeros((tile_size, tile_size, 3), dtype=np.uint8)
                padded[:tile.shape[0], :tile.shape[1]] = tile
                tile = padded

            # Apply maritime contrast enhancement
            tile = enhance_maritime_contrast(tile)

            # Save tile
            tile_name = f"{stem}_x{x}_y{y}.png"
            tile_path = output_dir / tile_name
            cv2.imwrite(str(tile_path), tile)
            tiles.append({
                "path": str(tile_path),
                "source": str(image_path),
                "x_offset": x,
                "y_offset": y,
                "tile_size": tile_size,
            })

    logger.info(f"Generated {len(tiles)} tiles from {image_path.name}")
    return tiles


def process_raw_directory(input_dir: Path, output_dir: Path,
                          tile_size: int = 640, overlap: int = 64):
    """Process all raw images in a directory."""
    supported_extensions = {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".jp2"}

    image_files = [
        f for f in input_dir.rglob("*")
        if f.suffix.lower() in supported_extensions
    ]

    if not image_files:
        logger.warning(f"No images found in {input_dir}")
        return

    logger.info(f"Found {len(image_files)} images to process")

    all_tiles = []
    for img_path in image_files:
        tiles = tile_image(img_path, output_dir, tile_size, overlap)
        all_tiles.extend(tiles)

    logger.info(f"Total tiles generated: {len(all_tiles)}")
    return all_tiles


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Preprocess and tile satellite imagery for ship detection"
    )
    parser.add_argument("--input", default=str(PROJECT_ROOT / "datasets" / "raw"),
                        help="Input directory with raw images")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "datasets" / "images" / "train"),
                        help="Output directory for processed tiles")
    parser.add_argument("--tile-size", type=int, default=640,
                        help="Tile size in pixels (default: 640)")
    parser.add_argument("--overlap", type=int, default=64,
                        help="Overlap between tiles (default: 64)")
    args = parser.parse_args()

    process_raw_directory(
        Path(args.input), Path(args.output),
        args.tile_size, args.overlap
    )
