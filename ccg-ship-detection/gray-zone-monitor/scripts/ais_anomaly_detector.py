#!/usr/bin/env python3
"""
Taiwan Gray Zone Monitor - AIS 異常偵測器
基於 CSIS「Signals in the Swarm」方法論

偵測灰色地帶行為指標:
- AIS 暗船 (Going Dark): 船隻關閉 AIS 信號
- 身份切換: MMSI 更改
- 非漁業滯留: 漁船在軍演區長時間停留但無捕魚行為
- 協同行動: 多船協調移動模式
"""

import json
import logging
import csv
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field, asdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MONITOR_ROOT = PROJECT_ROOT


@dataclass
class AISRecord:
    """單筆 AIS 位置記錄。"""
    mmsi: str
    timestamp: str
    lat: float
    lon: float
    speed: float = 0.0
    course: float = 0.0
    ship_type: str = ""
    flag: str = ""
    name: str = ""


@dataclass
class AnomalyEvent:
    """偵測到的異常事件。"""
    event_type: str       # ais_dark, identity_switch, militia_loiter, coordinated_movement
    mmsi: str
    severity: str         # low, medium, high, critical
    timestamp_start: str
    timestamp_end: str = ""
    lat: float = 0.0
    lon: float = 0.0
    details: dict = field(default_factory=dict)
    zone: str = ""


def load_monitor_config() -> dict:
    """載入監測設定。"""
    config_path = MONITOR_ROOT / "configs" / "monitor_config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_gray_zone_classes() -> dict:
    """載入灰色地帶行為分類。"""
    config_path = MONITOR_ROOT / "configs" / "gray_zone_classes.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def point_in_bbox(lat: float, lon: float, bbox: list) -> bool:
    """檢查點是否在 bounding box 內 [min_lon, min_lat, max_lon, max_lat]。"""
    return bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]


def parse_timestamp(ts: str) -> datetime:
    """解析 ISO 格式時間戳。"""
    for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    raise ValueError(f"無法解析時間戳: {ts}")


class AISAnomalyDetector:
    """
    AIS 異常偵測引擎。

    實現 CSIS Signals in the Swarm 的核心分析邏輯:
    1. 從 AIS 資料串流或 CSV 中讀取船舶位置記錄
    2. 按 MMSI 分組追蹤各船軌跡
    3. 偵測暗船事件、滯留行為、協同行動
    4. 輸出異常事件記錄
    """

    def __init__(self, config: dict = None):
        if config is None:
            config = load_monitor_config()
        self.config = config
        self.thresholds = config.get("alert_thresholds", {})
        self.zones = config.get("monitoring_zones", [])

        # 按 MMSI 索引的軌跡資料
        self.tracks = defaultdict(list)
        # 偵測到的異常事件
        self.anomalies = []

    def ingest_ais_csv(self, csv_path: str):
        """
        從 CSV 檔案載入 AIS 資料。

        預期欄位: mmsi, timestamp, lat, lon, speed, course, ship_type, flag, name
        """
        csv_file = Path(csv_path)
        if not csv_file.exists():
            logger.error(f"找不到 AIS 資料檔: {csv_path}")
            return

        count = 0
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                record = AISRecord(
                    mmsi=row.get("mmsi", row.get("MMSI", "")),
                    timestamp=row.get("timestamp", row.get("BaseDateTime", "")),
                    lat=float(row.get("lat", row.get("LAT", 0))),
                    lon=float(row.get("lon", row.get("LON", 0))),
                    speed=float(row.get("speed", row.get("SOG", 0))),
                    course=float(row.get("course", row.get("COG", 0))),
                    ship_type=row.get("ship_type", row.get("VesselType", "")),
                    flag=row.get("flag", row.get("Flag", "")),
                    name=row.get("name", row.get("VesselName", "")),
                )
                self.tracks[record.mmsi].append(record)
                count += 1

        # 按時間排序各軌跡
        for mmsi in self.tracks:
            self.tracks[mmsi].sort(key=lambda r: r.timestamp)

        logger.info(f"載入 {count} 筆 AIS 記錄，{len(self.tracks)} 艘船舶")

    def detect_ais_dark(self, gap_hours: float = None) -> list:
        """
        偵測 AIS 暗船事件 (Going Dark)。

        當船隻 AIS 信號消失超過閾值時間後又重新出現，
        判定為可能的 AIS 關閉事件。

        Args:
            gap_hours: AIS 信號間隔閾值（小時），超過此值判定為暗船事件
        """
        if gap_hours is None:
            gap_hours = self.thresholds.get("ais_dark_hours", 6)

        dark_events = []

        for mmsi, records in self.tracks.items():
            if len(records) < 2:
                continue

            for i in range(1, len(records)):
                prev = records[i - 1]
                curr = records[i]

                try:
                    t_prev = parse_timestamp(prev.timestamp)
                    t_curr = parse_timestamp(curr.timestamp)
                except ValueError:
                    continue

                gap = (t_curr - t_prev).total_seconds() / 3600.0

                if gap >= gap_hours:
                    # 檢查是否在監測區域內
                    zone_name = self._find_zone(prev.lat, prev.lon)

                    severity = "medium"
                    if gap >= gap_hours * 4:
                        severity = "critical"
                    elif gap >= gap_hours * 2:
                        severity = "high"

                    event = AnomalyEvent(
                        event_type="ais_dark",
                        mmsi=mmsi,
                        severity=severity,
                        timestamp_start=prev.timestamp,
                        timestamp_end=curr.timestamp,
                        lat=prev.lat,
                        lon=prev.lon,
                        zone=zone_name or "unknown",
                        details={
                            "gap_hours": round(gap, 1),
                            "last_position": {"lat": prev.lat, "lon": prev.lon},
                            "reappear_position": {"lat": curr.lat, "lon": curr.lon},
                            "vessel_name": prev.name,
                            "flag": prev.flag,
                            "ship_type": prev.ship_type,
                        }
                    )
                    dark_events.append(event)

        self.anomalies.extend(dark_events)
        logger.info(f"偵測到 {len(dark_events)} 起 AIS 暗船事件 (閾值: {gap_hours}h)")
        return dark_events

    def detect_militia_loitering(self, loiter_hours: float = None) -> list:
        """
        偵測疑似海上民兵滯留行為。

        篩選條件 (CSIS 方法):
        - 中國旗籍漁船
        - 在軍演區停留超過閾值時間
        - 低速或漂流行為（非正常捕魚模式）
        """
        if loiter_hours is None:
            loiter_hours = self.thresholds.get("loitering_hours_in_drill_zone", 72)

        militia_events = []

        for mmsi, records in self.tracks.items():
            # 僅篩選中國旗籍船隻
            flags = {r.flag.upper() for r in records if r.flag}
            is_chinese = any(f in flags for f in ["CN", "CHN", "CHINA", "中國"])
            if not is_chinese:
                continue

            # 檢查是否為漁船類型
            ship_types = {r.ship_type for r in records if r.ship_type}
            is_fishing = any("fish" in st.lower() or "30" in st for st in ship_types)

            # 計算在各監測區的停留時間
            zone_time = defaultdict(float)
            zone_records = defaultdict(list)

            for i in range(1, len(records)):
                prev = records[i - 1]
                curr = records[i]

                zone = self._find_zone(prev.lat, prev.lon)
                if zone:
                    try:
                        t_prev = parse_timestamp(prev.timestamp)
                        t_curr = parse_timestamp(curr.timestamp)
                        hours = (t_curr - t_prev).total_seconds() / 3600.0
                        if hours < 48:  # 排除資料間隔過大的情況
                            zone_time[zone] += hours
                            zone_records[zone].append(prev)
                    except ValueError:
                        continue

            # 檢查是否超過滯留閾值
            for zone, hours in zone_time.items():
                if hours >= loiter_hours:
                    # 計算平均速度（低速 = 非捕魚行為）
                    speeds = [r.speed for r in zone_records[zone] if r.speed >= 0]
                    avg_speed = sum(speeds) / len(speeds) if speeds else 0

                    severity = "high" if is_fishing else "medium"
                    if hours >= loiter_hours * 2:
                        severity = "critical"

                    event = AnomalyEvent(
                        event_type="militia_loiter",
                        mmsi=mmsi,
                        severity=severity,
                        timestamp_start=zone_records[zone][0].timestamp,
                        timestamp_end=zone_records[zone][-1].timestamp,
                        lat=zone_records[zone][0].lat,
                        lon=zone_records[zone][0].lon,
                        zone=zone,
                        details={
                            "loiter_hours": round(hours, 1),
                            "avg_speed_knots": round(avg_speed, 1),
                            "is_fishing_vessel": is_fishing,
                            "flag": list(flags),
                            "vessel_name": records[0].name,
                            "record_count": len(zone_records[zone]),
                        }
                    )
                    militia_events.append(event)

        self.anomalies.extend(militia_events)
        logger.info(f"偵測到 {len(militia_events)} 起疑似民兵滯留事件 (閾值: {loiter_hours}h)")
        return militia_events

    def detect_identity_switch(self) -> list:
        """
        偵測 MMSI 身份切換。

        分析同一船名但使用不同 MMSI 的情況，
        或同一 MMSI 對應不同船名的情況。
        """
        # 船名 -> MMSI 集合
        name_to_mmsi = defaultdict(set)
        # MMSI -> 船名集合
        mmsi_to_name = defaultdict(set)

        for mmsi, records in self.tracks.items():
            for r in records:
                if r.name:
                    name_to_mmsi[r.name].add(mmsi)
                    mmsi_to_name[mmsi].add(r.name)

        switch_events = []

        # 同一 MMSI 多個船名
        for mmsi, names in mmsi_to_name.items():
            if len(names) > 1:
                records = self.tracks[mmsi]
                event = AnomalyEvent(
                    event_type="identity_switch",
                    mmsi=mmsi,
                    severity="high",
                    timestamp_start=records[0].timestamp,
                    timestamp_end=records[-1].timestamp,
                    lat=records[0].lat,
                    lon=records[0].lon,
                    zone=self._find_zone(records[0].lat, records[0].lon) or "unknown",
                    details={
                        "switch_type": "mmsi_multiple_names",
                        "names": list(names),
                        "mmsi": mmsi,
                    }
                )
                switch_events.append(event)

        # 同一船名多個 MMSI
        for name, mmsis in name_to_mmsi.items():
            if len(mmsis) > 1:
                first_mmsi = list(mmsis)[0]
                records = self.tracks.get(first_mmsi, [])
                if records:
                    event = AnomalyEvent(
                        event_type="identity_switch",
                        mmsi=first_mmsi,
                        severity="high",
                        timestamp_start=records[0].timestamp,
                        zone=self._find_zone(records[0].lat, records[0].lon) or "unknown",
                        details={
                            "switch_type": "name_multiple_mmsi",
                            "name": name,
                            "mmsis": list(mmsis),
                        }
                    )
                    switch_events.append(event)

        self.anomalies.extend(switch_events)
        logger.info(f"偵測到 {len(switch_events)} 起身份切換事件")
        return switch_events

    def _find_zone(self, lat: float, lon: float) -> str:
        """找出座標所在的監測區域名稱。"""
        for zone in self.zones:
            bbox = zone.get("bbox")
            if bbox and point_in_bbox(lat, lon, bbox):
                return zone["name"]
            # 處理有子區域的情況（如海底電纜走廊）
            for sub_zone in zone.get("zones", []):
                if point_in_bbox(lat, lon, sub_zone["bbox"]):
                    return f"{zone['name']} - {sub_zone['name']}"
        return ""

    def run_all_detections(self) -> list:
        """執行所有異常偵測。"""
        logger.info("\n=== 開始灰色地帶異常偵測 ===\n")

        self.detect_ais_dark()
        self.detect_militia_loitering()
        self.detect_identity_switch()

        # 按嚴重性排序
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        self.anomalies.sort(key=lambda e: severity_order.get(e.severity, 9))

        logger.info(f"\n=== 偵測完成: 共 {len(self.anomalies)} 起異常事件 ===")

        # 統計
        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        for a in self.anomalies:
            by_type[a.event_type] += 1
            by_severity[a.severity] += 1

        logger.info("\n事件類型分布:")
        for t, c in by_type.items():
            logger.info(f"  {t}: {c}")

        logger.info("\n嚴重性分布:")
        for s, c in by_severity.items():
            logger.info(f"  {s}: {c}")

        return self.anomalies

    def export_events(self, output_path: str = None):
        """匯出異常事件為 JSON。"""
        if output_path is None:
            output_dir = MONITOR_ROOT / "data" / "ais_anomalies"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(output_dir / f"anomalies_{timestamp}.json")

        events = [asdict(a) for a in self.anomalies]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "total_events": len(events),
                "events": events,
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"異常事件已匯出: {output_path}")
        return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AIS 異常偵測器 - 台灣灰色地帶監測")
    parser.add_argument("--ais-csv", help="AIS 資料 CSV 檔案路徑")
    parser.add_argument("--dark-hours", type=float, help="暗船事件閾值（小時）")
    parser.add_argument("--loiter-hours", type=float, help="民兵滯留閾值（小時）")
    parser.add_argument("--output", help="異常事件輸出路徑")
    parser.add_argument(
        "--demo", action="store_true",
        help="使用示範資料執行偵測（展示功能）"
    )

    args = parser.parse_args()

    detector = AISAnomalyDetector()

    if args.ais_csv:
        detector.ingest_ais_csv(args.ais_csv)
        detector.run_all_detections()
        detector.export_events(args.output)

    elif args.demo:
        logger.info("=== 示範模式 ===")
        logger.info("本偵測器可接受以下格式的 AIS 資料:")
        logger.info("  CSV 欄位: mmsi, timestamp, lat, lon, speed, course, ship_type, flag, name")
        logger.info("")
        logger.info("資料來源建議:")
        logger.info("  1. Global Fishing Watch: https://globalfishingwatch.org/")
        logger.info("  2. MarineTraffic 歷史資料: https://www.marinetraffic.com/")
        logger.info("  3. AIS Hub: https://www.aishub.net/")
        logger.info("")
        logger.info("使用方式:")
        logger.info("  python ais_anomaly_detector.py --ais-csv data/ais_taiwan_strait.csv")
        logger.info("")
        logger.info("CSIS 方法論參考:")
        logger.info("  - 128/315 中國旗籍漁船被標記為灰色地帶行為者")
        logger.info("  - 閾值: AIS 暗船 >6 小時, 軍演區滯留 >72 小時")

    else:
        parser.print_help()
