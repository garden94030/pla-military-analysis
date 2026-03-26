#!/usr/bin/env python3
"""
Taiwan Gray Zone Monitor - 多源事件整合器
整合來自不同來源的灰色地帶事件，產生統一的威脅態勢報告。

整合來源:
- AIS 異常偵測器 (ais_anomaly_detector.py)
- ADIZ 入侵追蹤器 (adiz_tracker.py)
- CCG 船舶偵測結果 (ccg-ship-detection)
- 加拿大 DVD 暗船偵測
- CSIS Shadow Signals 資料
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MONITOR_ROOT = Path(__file__).resolve().parent.parent


class IncidentAggregator:
    """
    多源灰色地帶事件整合引擎。

    整合不同偵測來源的事件，消除重複，
    並產生統一的威脅態勢評估。
    """

    # 威脅等級定義 (基於 CSIS 建議的分級框架)
    THREAT_LEVELS = {
        "GREEN":  "正常活動水準",
        "YELLOW": "升高的灰色地帶活動",
        "ORANGE": "顯著的灰色地帶升級",
        "RED":    "準軍事危機或衝突前兆",
    }

    def __init__(self):
        self.events = []
        self.sources = set()

    def load_ais_anomalies(self, json_path: str):
        """載入 AIS 異常偵測結果。"""
        path = Path(json_path)
        if not path.exists():
            logger.warning(f"找不到: {json_path}")
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for event in data.get("events", []):
            self.events.append({
                "source": "ais_anomaly_detector",
                "type": event["event_type"],
                "severity": event["severity"],
                "timestamp": event.get("timestamp_start", ""),
                "location": {"lat": event.get("lat", 0), "lon": event.get("lon", 0)},
                "zone": event.get("zone", ""),
                "details": event.get("details", {}),
                "mmsi": event.get("mmsi", ""),
            })

        self.sources.add("ais_anomaly_detector")
        logger.info(f"載入 {len(data.get('events', []))} 筆 AIS 異常事件")

    def load_adiz_analysis(self, json_path: str):
        """載入 ADIZ 入侵分析結果。"""
        path = Path(json_path)
        if not path.exists():
            logger.warning(f"找不到: {json_path}")
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for surge in data.get("surge_events", []):
            self.events.append({
                "source": "adiz_tracker",
                "type": "adiz_surge",
                "severity": surge["severity"],
                "timestamp": surge["date"],
                "location": {"lat": 23.5, "lon": 119.5},  # 台灣 ADIZ 中心概略位置
                "zone": "Taiwan ADIZ",
                "details": {
                    "aircraft_count": surge["aircraft_count"],
                    "previous_avg": surge["previous_7day_avg"],
                    "ratio": surge["ratio"],
                },
            })

        self.sources.add("adiz_tracker")
        logger.info(f"載入 {len(data.get('surge_events', []))} 筆 ADIZ 升級事件")

    def load_satellite_detections(self, json_path: str):
        """載入衛星影像偵測結果 (CCG ship detection 輸出)。"""
        path = Path(json_path)
        if not path.exists():
            logger.warning(f"找不到: {json_path}")
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for detection in data.get("detections", []):
            self.events.append({
                "source": "satellite_detection",
                "type": f"vessel_detected_{detection.get('class', 'unknown')}",
                "severity": "medium",
                "timestamp": detection.get("timestamp", ""),
                "location": detection.get("location", {}),
                "zone": detection.get("zone", ""),
                "details": detection,
            })

        self.sources.add("satellite_detection")

    def assess_threat_level(self) -> dict:
        """
        評估當前威脅等級。

        基於多維度指標的加權評分:
        - AIS 暗船事件數量與嚴重性
        - ADIZ 入侵架次與頻率
        - CCG 大型船舶部署
        - 科考船活動密度
        - 軍事演習規模
        """
        if not self.events:
            return {"level": "GREEN", "score": 0, "description": self.THREAT_LEVELS["GREEN"]}

        # 計算威脅分數
        score = 0
        severity_weights = {"critical": 10, "high": 5, "medium": 2, "low": 1}
        type_weights = {
            "ais_dark": 3,
            "militia_loiter": 5,
            "identity_switch": 4,
            "adiz_surge": 8,
            "vessel_detected_ccg_large_cutter": 6,
            "vessel_detected_prc_research_vessel": 4,
        }

        for event in self.events:
            base = severity_weights.get(event["severity"], 1)
            type_mult = type_weights.get(event["type"], 1)
            score += base * type_mult

        # 正規化分數 (0-100)
        normalized = min(100, score / max(len(self.events), 1) * 10)

        if normalized >= 75:
            level = "RED"
        elif normalized >= 50:
            level = "ORANGE"
        elif normalized >= 25:
            level = "YELLOW"
        else:
            level = "GREEN"

        return {
            "level": level,
            "score": round(normalized, 1),
            "raw_score": score,
            "description": self.THREAT_LEVELS[level],
            "event_count": len(self.events),
            "sources": list(self.sources),
        }

    def generate_report(self, output_path: str = None) -> dict:
        """產生統一的態勢報告。"""
        threat = self.assess_threat_level()

        # 按區域統計
        by_zone = defaultdict(list)
        by_type = defaultdict(int)
        by_severity = defaultdict(int)

        for event in self.events:
            zone = event.get("zone", "Unknown")
            by_zone[zone].append(event)
            by_type[event["type"]] += 1
            by_severity[event["severity"]] += 1

        report = {
            "report_title": "台灣灰色地帶態勢報告 (Taiwan Gray Zone Situation Report)",
            "generated_at": datetime.now().isoformat(),
            "threat_assessment": threat,
            "event_summary": {
                "total_events": len(self.events),
                "by_type": dict(by_type),
                "by_severity": dict(by_severity),
                "by_zone": {z: len(events) for z, events in by_zone.items()},
            },
            "zone_details": {},
            "data_sources": list(self.sources),
            "recommendations": self._generate_recommendations(threat, by_type),
        }

        # 各區域詳細事件
        for zone, events in by_zone.items():
            report["zone_details"][zone] = {
                "event_count": len(events),
                "critical_events": len([e for e in events if e["severity"] == "critical"]),
                "latest_event": max(events, key=lambda e: e.get("timestamp", ""))
                if events else None,
            }

        # 印出報告
        self._print_report(report)

        # 儲存報告
        if output_path is None:
            output_dir = MONITOR_ROOT / "data" / "incidents"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(output_dir / f"sitrep_{timestamp}.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"\n態勢報告已儲存: {output_path}")
        return report

    def _generate_recommendations(self, threat: dict, by_type: dict) -> list:
        """
        基於威脅評估產生建議。
        參考 CSIS 政策建議框架。
        """
        recs = []

        if threat["level"] in ["RED", "ORANGE"]:
            recs.append(
                "建議啟動 Coalition Joint-Maritime Anomaly Cell (CJ-MAC) "
                "自動化異常偵測與即時監控 (CSIS 建議)"
            )

        if by_type.get("ais_dark", 0) > 5:
            recs.append(
                "大量 AIS 暗船事件: 建議增加衛星偵測頻率，"
                "並與加拿大 DVD 計畫數據交叉比對"
            )

        if by_type.get("militia_loiter", 0) > 0:
            recs.append(
                "偵測到疑似海上民兵活動: 建議公布違規船舶黑名單 "
                "(CSIS 建議: publish and punish blacklist)"
            )

        if by_type.get("adiz_surge", 0) > 0:
            recs.append(
                "ADIZ 入侵升級: 建議提高戰備等級並增加空中巡邏頻率"
            )

        if not recs:
            recs.append("目前威脅水準正常，建議維持例行監測。")

        return recs

    def _print_report(self, report: dict):
        """印出態勢報告。"""
        t = report["threat_assessment"]

        logger.info(f"\n{'='*60}")
        logger.info(f"台灣灰色地帶態勢報告")
        logger.info(f"生成時間: {report['generated_at']}")
        logger.info(f"{'='*60}")
        logger.info(f"\n  威脅等級: [{t['level']}] {t['description']}")
        logger.info(f"  威脅分數: {t['score']}/100")
        logger.info(f"  事件總數: {t['event_count']}")
        logger.info(f"  資料來源: {', '.join(t['sources'])}")

        es = report["event_summary"]
        logger.info(f"\n事件類型分布:")
        for typ, count in es["by_type"].items():
            logger.info(f"  {typ}: {count}")

        logger.info(f"\n嚴重性分布:")
        for sev, count in es["by_severity"].items():
            logger.info(f"  {sev}: {count}")

        logger.info(f"\n區域分布:")
        for zone, count in es["by_zone"].items():
            logger.info(f"  {zone}: {count} 起事件")

        logger.info(f"\n建議措施:")
        for i, rec in enumerate(report["recommendations"], 1):
            logger.info(f"  {i}. {rec}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="灰色地帶事件整合器 - 態勢報告產生器")
    parser.add_argument("--ais", help="AIS 異常事件 JSON 路徑")
    parser.add_argument("--adiz", help="ADIZ 分析結果 JSON 路徑")
    parser.add_argument("--satellite", help="衛星偵測結果 JSON 路徑")
    parser.add_argument("--output", help="報告輸出路徑")

    args = parser.parse_args()

    aggregator = IncidentAggregator()

    if args.ais:
        aggregator.load_ais_anomalies(args.ais)
    if args.adiz:
        aggregator.load_adiz_analysis(args.adiz)
    if args.satellite:
        aggregator.load_satellite_detections(args.satellite)

    if aggregator.events:
        aggregator.generate_report(args.output)
    else:
        logger.info("未載入任何事件資料。請提供至少一個資料來源:")
        logger.info("  --ais    : AIS 異常偵測結果")
        logger.info("  --adiz   : ADIZ 入侵分析結果")
        logger.info("  --satellite : 衛星偵測結果")
