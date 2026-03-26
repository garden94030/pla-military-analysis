# Annotation Guidelines (標註規範)

## Overview

This document defines the annotation standards for the CCG Ship Detection dataset.
Consistent labeling is critical for training accurate detection models.

---

## Annotation Format

**Primary format:** YOLO v8 (normalized center-xywh)

```
<class_id> <x_center> <y_center> <width> <height>
```

All coordinates are normalized to [0, 1] relative to image dimensions.

---

## Labeling Rules

### 1. Bounding Box Standards

- **Tight boxes**: Draw the smallest axis-aligned rectangle that fully encloses the vessel hull
- **Include wake**: Do NOT include the ship's wake in the bounding box
- **Partial vessels**: If a vessel is partially visible at the image edge, annotate
  only if >50% of the hull is visible
- **Overlapping vessels**: Annotate each vessel separately with its own bounding box

### 2. Class Assignment

| Class | When to Use |
|-------|-------------|
| 0 - ccg_large_cutter | Vessels >150m, identifiable as CCG mega-cutter class |
| 1 - ccg_medium_cutter | Vessels 100-130m, medium CCG patrol vessels |
| 2 - ccg_patrol_boat | Vessels 60-80m, standard patrol boats |
| 3 - ccg_fast_attack_craft | Small boats <40m, fast patrol craft |
| 4 - ccg_auxiliary | Non-combat support vessels (supply, survey, etc.) |

### 3. Difficult Cases

- **Uncertain class**: If vessel size is ambiguous between two classes, choose the
  larger class and add a note in the metadata
- **Non-CCG vessels**: Do NOT annotate civilian fishing boats, commercial shipping,
  or other nations' vessels — these are negative examples
- **Maritime militia**: If a vessel appears to be Chinese maritime militia (CMM),
  do NOT annotate as CCG. CMM detection is a separate task
- **Moored vessels**: Annotate vessels in port/moored only if clearly identifiable as CCG

### 4. Quality Criteria

Each annotation must meet:
- [ ] Bounding box tightly encloses the vessel hull
- [ ] Correct class ID assigned
- [ ] No duplicate annotations on the same vessel
- [ ] Coordinates within [0, 1] range
- [ ] Box width and height > 0

---

## Annotation Workflow

```
1. Open image in labelImg / CVAT
2. Identify all CCG vessels in the image
3. For each vessel:
   a. Estimate size using known image resolution
   b. Assign class based on size/type
   c. Draw tight bounding box around hull
4. Save in YOLO format
5. Run validate_dataset.py to check errors
```

---

## Cross-Reference with AIS/DVD Data

When available, cross-reference annotations with:

1. **AIS track data** — Confirm vessel identity via MMSI/IMO number
2. **Canada DVD detections** — Validate dark vessel positions
3. **PCG public reports** — Use Commodore Tarriela's published detection maps
4. **Known hull numbers** — Match satellite imagery to known CCG vessels (e.g., 5901, 2901, 3901)

### Example: CCG 5901 Track Reference

Based on the February 14, 2025 detection (Canada DVD / PCG):
- Position: 60.6 NM from Paracel Islands at 17:00H
- Track history: Sanya → Scarborough Shoal area → Recto Bank → Paracels
- 46-day continuous deployment since December 30, 2024
- This provides ground truth for satellite imagery collected on the same dates

---

## Image Metadata to Record

For each annotated image, maintain metadata:

```json
{
  "image_id": "sentinel2_abc123_x0_y640",
  "source": "sentinel2",
  "acquisition_date": "2025-02-14T09:30:00Z",
  "resolution_m": 10,
  "region": "South China Sea - Paracel Islands",
  "cloud_cover_pct": 5.2,
  "annotations_count": 3,
  "verified": false,
  "cross_reference": "PCG DVD detection 2025-02-14"
}
```

---

## Common Annotation Errors to Avoid

1. **Too loose boxes** — Excess water around the vessel
2. **Including wake** — Wake should not be part of the bounding box
3. **Wrong class** — Double-check vessel size against resolution
4. **Missing vessels** — Carefully scan entire image, especially at edges
5. **Duplicate boxes** — One box per vessel only
