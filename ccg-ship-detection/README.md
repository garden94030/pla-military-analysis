# CCG Ship Detection Dataset (中共海警船偵測資料集)

## Project Overview

This project builds a satellite/aerial imagery dataset for detecting **China Coast Guard (CCG / 中共海警)** vessels. The dataset supports training object detection models (YOLOv8, Faster R-CNN, etc.) to automatically identify CCG ships in maritime surveillance imagery.

## Target Vessel Classes

| Class ID | English | 中文 | Description |
|----------|---------|------|-------------|
| 0 | CCG Large Cutter | 海警大型巡邏艦 | 10,000+ ton class (e.g., CCG 2901, CCG 3901) |
| 1 | CCG Medium Cutter | 海警中型巡邏艦 | 3,000-5,000 ton class (e.g., Type 818) |
| 2 | CCG Patrol Boat | 海警巡邏艇 | 1,000-1,500 ton class |
| 3 | CCG Fast Attack Craft | 海警快艇 | Small fast patrol boats |
| 4 | CCG Auxiliary | 海警輔助船 | Supply, survey, and support vessels |

## Directory Structure

```
ccg-ship-detection/
├── README.md                  # This file
├── datasets/
│   ├── images/
│   │   ├── train/             # Training images (70%)
│   │   ├── val/               # Validation images (15%)
│   │   └── test/              # Test images (15%)
│   ├── labels/
│   │   ├── train/             # YOLO format annotations
│   │   ├── val/
│   │   └── test/
│   └── raw/                   # Unprocessed source imagery
├── scripts/
│   ├── collect_imagery.py     # Satellite imagery collection
│   ├── preprocess.py          # Image preprocessing & tiling
│   ├── annotate.py            # Annotation helper tools
│   ├── convert_annotations.py # Format conversion (YOLO/COCO/VOC)
│   ├── augment.py             # Data augmentation pipeline
│   ├── split_dataset.py       # Train/val/test splitting
│   └── validate_dataset.py    # Dataset integrity checks
├── configs/
│   ├── dataset.yaml           # YOLOv8 dataset config
│   ├── classes.json           # Class definitions
│   └── collection_sources.json # Imagery source config
├── docs/
│   ├── vessel_identification_guide.md  # CCG vessel ID guide
│   └── annotation_guidelines.md        # Labeling standards
└── models/
    └── .gitkeep               # Trained model weights (excluded from git)
```

## Quick Start

### 1. Setup Environment

```bash
pip install -r requirements.txt
```

### 2. Collect Imagery

```bash
python scripts/collect_imagery.py --config configs/collection_sources.json
```

### 3. Preprocess & Tile

```bash
python scripts/preprocess.py --input datasets/raw --output datasets/images --tile-size 640
```

### 4. Annotate

```bash
python scripts/annotate.py --images datasets/images/train
```

### 5. Train Model

```bash
yolo detect train data=configs/dataset.yaml model=yolov8m.pt epochs=100 imgsz=640
```

## Data Sources

| Source | Type | Resolution | Access |
|--------|------|-----------|--------|
| Sentinel-2 | Optical satellite | 10m | Free (ESA Copernicus) |
| Sentinel-1 | SAR satellite | 5-20m | Free (ESA Copernicus) |
| Planet Labs | Optical satellite | 3-5m | Commercial API |
| Maxar | Optical satellite | 0.3-0.5m | Commercial API |
| SkyFi | Multi-source | Variable | Commercial API |
| AIS Data | Ship tracking | N/A | MarineTraffic / VesselFinder |

## Annotation Format

Primary format: **YOLO** (normalized xywh)

```
<class_id> <x_center> <y_center> <width> <height>
```

Example:
```
0 0.4521 0.3287 0.0834 0.0213
```

## License

For research and defense analysis purposes only.
