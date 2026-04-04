#!/usr/bin/env python3
"""
Taiwan Gray Zone Monitor - ADIZ 入侵追蹤器
台灣防空識別區入侵追蹤

追蹤 PLA 軍機進入台灣 ADIZ 的頻率、機型、路線模式。
資料來源: 台灣國防部每日公告 + Gerald C. Brown 彙整資料集
"""

import json
import csv
import logging
from datetime import datetime, date
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MONITOR_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class ADIZIncursion:
    """單次 ADIZ 入侵記錄。"""
    date: str
    aircraft_type: str
    aircraft_count: int = 1
    crossed_median_line: bool = False
    entered_southwest_adiz: bool = True
    exercise_name: str = ""
    notes: str = ""


class ADIZTracker:
    """
    ADIZ 入侵分析引擎。

    功能:
    - 載入歷史 ADIZ 入侵記錄
    - 趨勢分析（月/季/年）
    - 機型分類統計
    - 升級事件偵測（大規模入侵）
    - 與軍事演習事件的關聯分析
    """

    # PLA 常見入侵機型
    AIRCRAFT_TYPES = {
        "fighters": ["J-10", "J-11", "J-16", "J-16D", "Su-30"],
        "bombers": ["H-6", "H-6K", "H-6J", "H-6N"],
        "asw": ["Y-8 ASW", "KQ-200"],
        "elint": ["Y-8 EW", "Y-8 ELINT", "Y-9 EW"],
        "aew": ["KJ-500", "KJ-200"],
        "uav": ["BZK-005", "WZ-7", "TB-001"],
        "transport": ["Y-20", "Y-8", "Y-9"],
        "helicopter": ["Z-9", "Z-20"],
    }

    # 重大事件閾值
    ELEVATED_THRESHOLD = 10   # 單日 10 架次以上為 elevated
    CRITICAL_THRESHOLD = 30   # 單日 30 架次以上為 critical
    SURGE_THRESHOLD = 50      # 單日 50 架次以上為 surge (歷史最高級別)

    def __init__(self):
        self.records = []
        self.daily_totals = defaultdict(int)

    def load_csv(self, csv_path: str):
        """
        從 CSV 載入 ADIZ 入侵記錄。

        預期欄位: date, aircraft_type, count, median_line, sector, exercise, notes
        """
        csv_file = Path(csv_path)
        if not csv_file.exists():
            logger.error(f"找不到資料檔: {csv_path}")
            return

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                record = ADIZIncursion(
                    date=row.get("date", ""),
                    aircraft_type=row.get("aircraft_type", ""),
                    aircraft_count=int(row.get("count", row.get("aircraft_count", 1))),
                    crossed_median_line=row.get("median_line", "").lower() in ["true", "yes", "1"],
                    entered_southwest_adiz=row.get("sector", "sw").lower() in ["sw", "southwest", "西南"],
                    exercise_name=row.get("exercise", ""),
                    notes=row.get("notes", ""),
                )
                self.records.append(record)
                self.daily_totals[record.date] += record.aircraft_count

        logger.info(f"載入 {len(self.records)} 筆 ADIZ 入侵記錄")

    def add_record(self, record: ADIZIncursion):
        """新增單筆記錄。"""
        self.records.append(record)
        self.daily_totals[record.date] += record.aircraft_count

    def analyze_trends(self) -> dict:
        """分析入侵趨勢。"""
        if not self.records:
            logger.warning("無記錄可分析")
            return {}

        monthly = defaultdict(int)
        by_type_category = defaultdict(int)
        median_line_count = 0
        exercise_related = defaultdict(int)

        for r in self.records:
            # 月度統計
            if len(r.date) >= 7:
                month_key = r.date[:7]
                monthly[month_key] += r.aircraft_count

            # 機型分類
            for category, types in self.AIRCRAFT_TYPES.items():
                if any(t.lower() in r.aircraft_type.lower() for t in types):
                    by_type_category[category] += r.aircraft_count
                    break

            # 中線越界
            if r.crossed_median_line:
                median_line_count += r.aircraft_count

            # 演習相關
            if r.exercise_name:
                exercise_related[r.exercise_name] += r.aircraft_count

        # 找出高峰日
        peak_days = sorted(
            self.daily_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # 升級事件
        elevated_days = [
            (d, c) for d, c in self.daily_totals.items()
            if c >= self.ELEVATED_THRESHOLD
        ]
        critical_days = [
            (d, c) for d, c in self.daily_totals.items()
            if c >= self.CRITICAL_THRESHOLD
        ]

        total_aircraft = sum(r.aircraft_count for r in self.records)
        total_days = len(self.daily_totals)

        analysis = {
            "summary": {
                "total_records": len(self.records),
                "total_aircraft_sorties": total_aircraft,
                "total_days_with_incursions": total_days,
                "average_daily_sorties": round(total_aircraft / max(total_days, 1), 1),
                "median_line_crossings": median_line_count,
                "elevated_days": len(elevated_days),
                "critical_days": len(critical_days),
            },
            "monthly_totals": dict(sorted(monthly.items())),
            "aircraft_categories": dict(by_type_category),
            "peak_days": [{"date": d, "count": c} for d, c in peak_days],
            "exercise_related": dict(exercise_related),
        }

        # 印出分析結果
        self._print_analysis(analysis)

        return analysis

    def _print_analysis(self, analysis: dict):
        """印出分析結果。"""
        s = analysis["summary"]
        logger.info(f"\n{'='*60}")
        logger.info("台灣 ADIZ 入侵趨勢分析")
        logger.info(f"{'='*60}")
        logger.info(f"  總記錄數:         {s['total_records']}")
        logger.info(f"  總架次:           {s['total_aircraft_sorties']}")
        logger.info(f"  入侵天數:         {s['total_days_with_incursions']}")
        logger.info(f"  每日平均:         {s['average_daily_sorties']} 架次")
        logger.info(f"  中線越界:         {s['median_line_crossings']} 架次")
        logger.info(f"  升級事件 (>10架): {s['elevated_days']} 天")
        logger.info(f"  重大事件 (>30架): {s['critical_days']} 天")

        logger.info("\n機型類別分布:")
        for cat, count in analysis["aircraft_categories"].items():
            pct = count / max(s["total_aircraft_sorties"], 1) * 100
            logger.info(f"  {cat:15s}: {count:5d} ({pct:.1f}%)")

        if analysis["peak_days"]:
            logger.info("\n前 10 高峰日:")
            for item in analysis["peak_days"]:
                level = "CRITICAL" if item["count"] >= 30 else (
                    "ELEVATED" if item["count"] >= 10 else "")
                logger.info(f"  {item['date']}: {item['count']} 架次 {level}")

        if analysis["exercise_related"]:
            logger.info("\n演習相關入侵:")
            for ex, count in analysis["exercise_related"].items():
                logger.info(f"  {ex}: {count} 架次")

    def detect_surge_events(self) -> list:
        """偵測突然升級的入侵事件。"""
        surge_events = []
        dates = sorted(self.daily_totals.keys())

        for i, d in enumerate(dates):
            count = self.daily_totals[d]

            # 計算前 7 天的平均值
            prev_dates = dates[max(0, i-7):i]
            if prev_dates:
                avg_prev = sum(self.daily_totals[pd] for pd in prev_dates) / len(prev_dates)
            else:
                avg_prev = 0

            # 如果當日架次 > 前 7 日平均的 3 倍，或超過 elevated 閾值
            if (count >= self.ELEVATED_THRESHOLD or
                    (avg_prev > 0 and count >= avg_prev * 3)):
                severity = "critical" if count >= self.CRITICAL_THRESHOLD else "high"
                if count >= self.SURGE_THRESHOLD:
                    severity = "critical"

                surge_events.append({
                    "date": d,
                    "aircraft_count": count,
                    "severity": severity,
                    "previous_7day_avg": round(avg_prev, 1),
                    "ratio": round(count / max(avg_prev, 1), 1),
                })

        logger.info(f"偵測到 {len(surge_events)} 起升級事件")
        return surge_events

    def export_analysis(self, output_path: str = None):
        """匯出分析結果。"""
        if output_path is None:
            output_dir = MONITOR_ROOT / "data" / "adiz_violations"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(output_dir / f"adiz_analysis_{timestamp}.json")

        analysis = self.analyze_trends()
        analysis["surge_events"] = self.detect_surge_events()
        analysis["generated_at"] = datetime.now().isoformat()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        logger.info(f"分析結果已匯出: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ADIZ 入侵追蹤器 - 台灣灰色地帶監測")
    parser.add_argument("--csv", help="ADIZ 入侵記錄 CSV 路徑")
    parser.add_argument("--output", help="分析結果輸出路徑")
    parser.add_argument("--demo", action="store_true", help="使用示範資料展示功能")

    args = parser.parse_args()

    tracker = ADIZTracker()

    if args.csv:
        tracker.load_csv(args.csv)
        tracker.export_analysis(args.output)

    elif args.demo:
        logger.info("=== ADIZ 追蹤器示範模式 ===\n")
        logger.info("資料來源:")
        logger.info("  1. 台灣國防部每日公告: https://www.mnd.gov.tw/")
        logger.info("  2. Gerald C. Brown 彙整資料集 (Google Sheets)")
        logger.info("  3. Taiwan Security Monitor: https://tsm.schar.gmu.edu/")
        logger.info("")
        logger.info("CSV 格式:")
        logger.info("  date,aircraft_type,count,median_line,sector,exercise,notes")
        logger.info("  2024-10-14,J-16,6,no,SW,,")
        logger.info("  2024-10-14,H-6K,2,no,SW,,Joint Sword C")
        logger.info("")
        logger.info("使用方式:")
        logger.info("  python adiz_tracker.py --csv data/adiz_violations/adiz_2024.csv")

    else:
        parser.print_help()
