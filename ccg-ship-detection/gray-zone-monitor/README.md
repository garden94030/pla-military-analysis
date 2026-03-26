# Taiwan Gray Zone Monitor (台灣灰色地帶監測)

## 概述

本模組整合多種開源情報 (OSINT) 資料來源，監測中國對台灣的灰色地帶行動，
包括海上灰色地帶船舶偵測、ADIZ 侵入追蹤、海底電纜威脅評估，以及 AIS 異常偵測。

本模組與 `ccg-ship-detection` 衛星影像偵測專案協同運作，
提供從衛星影像到行為分析的完整態勢感知能力。

## 方法論

### CSIS「Signals in the Swarm」框架

本模組採用 CSIS Futures Lab 於 2025 年 10 月發表的分析框架：

1. **AIS 追蹤 + 漁業努力量資料** — 辨識非正常捕魚行為的船隻
2. **軍事演習區比對** — 標記長時間停留於演習區的民用船隻
3. **AIS 異常偵測** — 識別關閉 AIS（going dark）、更改識別碼等行為
4. **行為分類** — 將近 12,000 艘船隻篩選至 128 艘可能的灰色地帶行為者

### 資料來源

| 資料來源 | 類型 | 說明 |
|---------|------|------|
| Global Fishing Watch (GFW) | AIS + 漁業 | 全球漁船追蹤，免費開源 |
| MarineTraffic | AIS | 即時船舶追蹤 |
| Starboard Maritime Intelligence | AIS 分析 | 紐西蘭平台，Reuters 使用追蹤中國科考船 |
| Taiwan MND ADIZ Reports | 軍事 | 台灣國防部每日防空識別區入侵通報 |
| Canada DVD Program | 暗船偵測 | 加拿大暗船偵測衛星計畫 |
| CSIS Shadow Signals | 多源融合 | AIS + ADS-B + 商業衛星 + 環境資料 |
| Taiwan Security Monitor (TSM) | OSINT | 喬治梅森大學，含 CCG 事件追蹤器 |
| CCG Ship Detection (本專案) | 衛星影像 | 自動偵測海警船與科考船 |

## 監測範疇

### 1. 海上灰色地帶 (Maritime Gray Zone)
- 海警船巡邏模式分析
- 海上民兵 (Maritime Militia) 船隊追蹤
- 灰色地帶船舶行為分類（CSIS 框架）
- 暗船偵測（AIS 關閉事件）

### 2. 空域灰色地帶 (Airspace Gray Zone)
- ADIZ 入侵次數與機型追蹤
- 中線越界事件
- 戰鬥空中巡邏 (CAP) 模式分析

### 3. 海底基礎設施威脅 (Subsea Infrastructure)
- 海底電纜附近可疑活動
- 科考船佈署感測器追蹤（透明海洋計畫）
- 呂宋海峽感測器佈署監測

### 4. 認知作戰指標 (Cognitive Warfare Indicators)
- 軍事演習頻率與規模趨勢
- 「聯合利劍」(Joint Sword) 演習模式
- 經濟脅迫事件追蹤

## 目錄結構

```
gray-zone-monitor/
├── README.md
├── configs/
│   ├── monitor_config.json      # 監測參數設定
│   └── gray_zone_classes.json   # 灰色地帶行為分類定義
├── scripts/
│   ├── ais_anomaly_detector.py  # AIS 異常偵測 (CSIS 方法)
│   ├── adiz_tracker.py          # ADIZ 入侵追蹤
│   ├── gfw_analyzer.py          # Global Fishing Watch 資料分析
│   ├── incident_aggregator.py   # 多源事件整合
│   └── threat_dashboard.py      # 威脅態勢儀表板
├── data/
│   ├── .gitkeep
│   ├── adiz_violations/         # ADIZ 入侵記錄
│   ├── ais_anomalies/           # AIS 異常事件
│   └── incidents/               # 灰色地帶事件記錄
└── docs/
    └── methodology.md           # 分析方法論詳述
```

## 參考來源

- [CSIS - Signals in the Swarm](https://www.csis.org/analysis/signals-swarm-data-behind-chinas-maritime-gray-zone-campaign-near-taiwan)
- [CSIS - Shadow Signals](https://www.csis.org/programs/futures-lab/projects/shadow-signals-using-big-data-and-geospatial-analysis-track-gray-zone)
- [Taiwan Security Monitor (GMU)](https://tsm.schar.gmu.edu/)
- [Global Taiwan Institute - Gray Zone Tactics](https://globaltaiwan.org/2024/03/decoding-beijings-gray-zone-tactics-china-coast-guard-activities-and-the-redefinition-of-conflict-in-the-taiwan-strait/)
- [CNAS - Resisting China's Gray Zone Military Pressure](https://www.cnas.org/publications/reports/resisting-chinas-gray-zone-military-pressure-on-taiwan)
- [Reuters 2026-03-24 - China Undersea Mapping Investigation](https://www.reuters.com)
