#!/usr/bin/env python3
"""
CCG Ship Detection - 示範資料產生器
產生模擬的衛星影像與標註資料，用於測試完整管線。

產生內容:
- 模擬海面背景影像 (640x640)
- 隨機放置不同大小的模擬船舶
- 對應的 YOLO 格式標註檔
"""

import random
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 各類船舶的像素大小範圍 (寬, 高) at 640x640 image
# 基於 10m/pixel Sentinel-2 解析度估算
VESSEL_SIZES = {
    0: {"name": "大型巡邏艦", "w": (12, 18), "h": (3, 5)},   # ~150-165m
    1: {"name": "中型巡邏艦", "w": (8, 13), "h": (2, 4)},    # ~100-130m
    2: {"name": "巡邏艇",     "w": (5, 8),  "h": (1, 3)},    # ~60-80m
    3: {"name": "快艇",       "w": (2, 4),  "h": (1, 2)},    # ~20-40m
    4: {"name": "輔助船",     "w": (4, 9),  "h": (1, 3)},    # ~50-90m
    5: {"name": "科考船",     "w": (6, 12), "h": (2, 3)},    # ~80-120m
}


def generate_ocean_background(width: int = 640, height: int = 640):
    """產生模擬海面背景。"""
    try:
        import numpy as np
    except ImportError:
        logger.error("需要 numpy: pip install numpy")
        return None

    # 深藍色海面基底 + 隨機噪點模擬海浪
    base_color = np.array([45, 60, 80], dtype=np.float32)  # BGR 深藍
    img = np.tile(base_color, (height, width, 1)).astype(np.float32)

    # 加入海浪噪點
    noise = np.random.normal(0, 8, (height, width, 3))
    img += noise

    # 加入大尺度亮度變化（模擬日照角度）
    gradient = np.linspace(0.85, 1.15, width).reshape(1, -1, 1)
    img *= gradient

    return np.clip(img, 0, 255).astype(np.uint8)


def draw_vessel(img, x_center: int, y_center: int, w: int, h: int,
                class_id: int, rotation: float = 0):
    """在影像上繪製模擬船舶。"""
    try:
        import numpy as np
        import cv2
    except ImportError:
        return img

    # 船舶顏色 (白/灰色船體)
    vessel_colors = {
        0: (220, 220, 230),  # 白色大型船
        1: (200, 200, 210),
        2: (190, 190, 200),
        3: (180, 180, 190),
        4: (170, 175, 185),
        5: (210, 215, 225),  # 白色科考船
    }
    color = vessel_colors.get(class_id, (200, 200, 210))

    # 繪製旋轉矩形
    rect = ((x_center, y_center), (w, h), rotation)
    box = cv2.boxPoints(rect).astype(int)
    cv2.fillConvexPoly(img, box, color)

    # 加入船舶亮點（模擬上層建築）
    bridge_w = max(2, w // 4)
    bridge_h = max(1, h // 2)
    bridge_offset = int(w * 0.2)
    bx = int(x_center + bridge_offset * np.cos(np.radians(rotation)))
    by = int(y_center + bridge_offset * np.sin(np.radians(rotation)))
    cv2.rectangle(
        img,
        (bx - bridge_w // 2, by - bridge_h // 2),
        (bx + bridge_w // 2, by + bridge_h // 2),
        (240, 240, 245),
        -1
    )

    # 繪製尾跡（V 形）
    wake_length = w * 2
    wake_color = (55, 70, 95)
    angle_rad = np.radians(rotation)
    tail_x = int(x_center - (w / 2 + 2) * np.cos(angle_rad))
    tail_y = int(y_center - (w / 2 + 2) * np.sin(angle_rad))

    for sign in [1, -1]:
        spread_angle = angle_rad + sign * np.radians(15)
        end_x = int(tail_x - wake_length * np.cos(spread_angle))
        end_y = int(tail_y - wake_length * np.sin(spread_angle))
        cv2.line(img, (tail_x, tail_y), (end_x, end_y), wake_color, 1)

    return img


def generate_sample_image(image_id: int, img_size: int = 640,
                           num_vessels: int = None) -> tuple:
    """
    產生一張模擬衛星影像及其標註。

    Returns:
        (image_array, annotations_list)
    """
    try:
        import numpy as np
    except ImportError:
        return None, []

    if num_vessels is None:
        num_vessels = random.randint(1, 5)

    img = generate_ocean_background(img_size, img_size)
    if img is None:
        return None, []

    annotations = []
    placed_boxes = []

    for _ in range(num_vessels):
        # 隨機選擇船舶類型（加權：大型船較少，巡邏艇較多）
        weights = [0.08, 0.15, 0.30, 0.20, 0.12, 0.15]
        class_id = random.choices(range(6), weights=weights, k=1)[0]

        size_info = VESSEL_SIZES[class_id]
        w = random.randint(*size_info["w"])
        h = random.randint(*size_info["h"])
        rotation = random.uniform(0, 360)

        # 隨機位置（避免邊緣和重疊）
        margin = max(w, h) + 5
        max_attempts = 50
        placed = False

        for _ in range(max_attempts):
            x = random.randint(margin, img_size - margin)
            y = random.randint(margin, img_size - margin)

            # 檢查是否與已放置的船舶重疊
            overlap = False
            for bx, by, bw, bh in placed_boxes:
                if (abs(x - bx) < (w + bw) / 2 + 10 and
                        abs(y - by) < (h + bh) / 2 + 10):
                    overlap = True
                    break

            if not overlap:
                placed = True
                break

        if not placed:
            continue

        # 繪製船舶
        img = draw_vessel(img, x, y, w, h, class_id, rotation)
        placed_boxes.append((x, y, w, h))

        # YOLO 格式標註 (normalized)
        x_norm = x / img_size
        y_norm = y / img_size
        w_norm = w / img_size
        h_norm = h / img_size

        annotations.append(
            f"{class_id} {x_norm:.6f} {y_norm:.6f} {w_norm:.6f} {h_norm:.6f}"
        )

    return img, annotations


def generate_demo_dataset(num_train: int = 30, num_val: int = 8, num_test: int = 8):
    """
    產生完整的示範資料集。

    Args:
        num_train: 訓練集影像數量
        num_val: 驗證集影像數量
        num_test: 測試集影像數量
    """
    try:
        import cv2
    except ImportError:
        logger.error("需要 opencv-python: pip install opencv-python")
        return

    splits = {
        "train": num_train,
        "val": num_val,
        "test": num_test,
    }

    total_images = 0
    total_objects = 0
    class_counts = {i: 0 for i in range(6)}

    for split_name, count in splits.items():
        img_dir = PROJECT_ROOT / "datasets" / "images" / split_name
        lbl_dir = PROJECT_ROOT / "datasets" / "labels" / split_name
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"\n產生 {split_name} 資料集: {count} 張影像")

        for i in range(count):
            img, annotations = generate_sample_image(i)
            if img is None:
                continue

            # 儲存影像
            img_name = f"demo_{split_name}_{i:04d}.png"
            cv2.imwrite(str(img_dir / img_name), img)

            # 儲存標註
            lbl_name = f"demo_{split_name}_{i:04d}.txt"
            with open(lbl_dir / lbl_name, "w") as f:
                f.write("\n".join(annotations))

            total_images += 1
            total_objects += len(annotations)

            for ann in annotations:
                cls_id = int(ann.split()[0])
                class_counts[cls_id] += 1

    # 統計報告
    logger.info(f"\n{'='*50}")
    logger.info("示範資料集產生完成")
    logger.info(f"{'='*50}")
    logger.info(f"  總影像數: {total_images}")
    logger.info(f"  總物件數: {total_objects}")
    logger.info(f"\n  類別分布:")
    for cls_id, count in class_counts.items():
        name = VESSEL_SIZES[cls_id]["name"]
        logger.info(f"    [{cls_id}] {name}: {count}")

    logger.info(f"\n  訓練集: {splits['train']} 張")
    logger.info(f"  驗證集: {splits['val']} 張")
    logger.info(f"  測試集: {splits['test']} 張")
    logger.info(f"\n  影像路徑: {PROJECT_ROOT / 'datasets' / 'images'}")
    logger.info(f"  標註路徑: {PROJECT_ROOT / 'datasets' / 'labels'}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="產生模擬衛星影像與標註的示範資料集"
    )
    parser.add_argument("--train", type=int, default=30, help="訓練集數量 (預設: 30)")
    parser.add_argument("--val", type=int, default=8, help="驗證集數量 (預設: 8)")
    parser.add_argument("--test", type=int, default=8, help="測試集數量 (預設: 8)")
    args = parser.parse_args()

    generate_demo_dataset(args.train, args.val, args.test)
