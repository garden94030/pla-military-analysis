# 🔄 Wiki Raw 自動化分析系統指南

## 🎯 系統概述

本系統自動監測 `wiki/raw/` 資料夾，將新檔案轉換為分析任務。解決了 raw/ 與 _daily_input/ 的重疊問題。

### 職責劃分（新模式）

```
┌─────────────────────────────────────────┐
│  Obsidian Web Clipper                  │
│  (自動倾倒網頁、PDF、截圖)             │
└─────────────────┬───────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ wiki/raw/      │ ← 「黑洞」
         │ (無腦倾倒區)    │   (自動化掃描)
         └────────┬───────┘
                  │
          [auto_analyze_raw.py]
                  │
                  ▼
    ┌────────────────────────────┐
    │ _daily_input/              │ ← 分析待列隊
    │ (auto_*.md 自動任務)        │   (準備分析)
    └────────┬───────────────────┘
             │
      [/daily-analysis]
             │
             ▼
      _daily_output/（分析報告）
```

## 🚀 工作流程

### 自動流程（無需操作）

1. **檔案倾倒**：將截圖/PDF/連結丟入 `wiki/raw/`
2. **自動偵測**：系統監測新檔案（每次 Write/Edit 後）
3. **自動轉移**：新檔案 → `_daily_input/` 生成分析任務卡
4. **準備分析**：任務卡標記為 `pending`（等待 `/daily-analysis`）
5. **執行分析**：手動或自動執行 `/daily-analysis` skill

### 手動觸發

```bash
# 掃描並處理所有新檔案
python auto_analyze_raw.py

# 處理單一檔案
python auto_analyze_raw.py --process-file "wiki/raw/image.jpg"

# 查看處理狀態
python auto_analyze_raw.py     # 輸出狀態報告
```

## 📋 生成的任務卡格式

自動轉移到 `_daily_input/` 的檔案：

```markdown
---
title: 【自動轉移】055驅逐艦演習
type: raw_input
source_file: HE7q-r2aUAAdBp4.jfif
status: pending
date: 2026-04-04T10:30:45
---

## 原始資料來源
- **檔案**: HE7q-r2aUAAdBp4.jfif
- **位置**: wiki/raw/HE7q-r2aUAAdBp4.jfif
- **接收時間**: 2026-04-04 10:30:45

## 分析待辦
- [ ] 提取地點/關鍵詞
- [ ] 生成初步分析
- [ ] 標記完成狀態

**備註**: 本檔案由自動化系統從 wiki/raw/ 轉移，建議進行進一步的手工審視。
```

## ⚙️ 組件說明

### 1. auto_analyze_raw.py
**功能**：掃描 raw/ 目錄，建立分析任務

| 模式 | 說明 |
|------|------|
| `python auto_analyze_raw.py` | 掃描並自動處理所有新檔案 |
| 異步 hook | 每次 Write/Edit 後自動檢查（背景執行） |

### 2. raw_processed.json
**位置**：`_system/raw_processed.json`

紀錄：
- 已處理的檔案清單
- 處理時間戳
- 轉移狀態

```json
{
  "processed_files": {
    "image.jpg": {
      "processed_at": "2026-04-04T10:30:45",
      "file_path": "/path/to/wiki/raw/image.jpg",
      "status": "converted_to_daily_input"
    }
  },
  "last_run": "2026-04-04T10:30:45"
}
```

### 3. PostToolUse Hook
**觸發**：每次 Write/Edit 後（背景非阻塞）

**動作**：
- 執行 `auto_analyze_raw.py`
- 檢查是否有新檔案
- 自動轉移到 _daily_input/
- 不影響主要工作流程

## 💡 使用建議

### ✅ 最佳實踐

1. **Obsidian Web Clipper 配置**
   ```
   保存路徑：wiki/raw/
   檔名模板：{{title | replace("/", "-")}}
   ```

2. **定期審視**
   - 每日查看 `_daily_input/auto_*.md` 的任務卡
   - 確認優先級和內容
   - 執行 `/daily-analysis`

3. **清理已分析**
   - 分析完成後將 `status` 改為 `completed`
   - raw_processed.json 自動追蹤

### ❌ 要避免的

- ❌ 同時在 raw/ 和 _daily_input/ 放檔案（會重複）
- ❌ 手動刪除 raw_processed.json（會導致重複處理）
- ❌ 直接在 raw/ 修改檔案（應移至 _daily_input/ 編輯）

## 🔧 故障排除

### 問題：raw/ 新檔案沒有自動轉移

**檢查清單**：
1. ✓ auto_analyze_raw.py 是否在專案根目錄
2. ✓ settings.json 中 PostToolUse hook 是否啟用
3. ✓ 檔案副檔名是否支援（.jpg/.pdf/.md/.txt）
4. ✓ raw_processed.json 是否可寫入

**手動觸發**：
```bash
python auto_analyze_raw.py
```

### 問題：同一檔案被重複處理

**原因**：raw_processed.json 損壞或遺失

**解決**：
```bash
# 清空處理記錄
python -c "import json; open('_system/raw_processed.json','w').write(json.dumps({'processed_files':{},'last_run':None}))"

# 重新掃描
python auto_analyze_raw.py
```

## 📊 監控命令

```bash
# 查看處理狀態
python auto_analyze_raw.py

# 檢查已處理檔案清單
python -c "import json; print(json.dumps(json.load(open('_system/raw_processed.json')), ensure_ascii=False, indent=2))"

# 統計待分析任務
ls -la _daily_input/auto_*.md | wc -l
```

## 🔮 未來改進

| 優先級 | 功能 | 說明 |
|--------|------|------|
| 🔴 高 | 圖片 OCR | 自動提取圖片中的文字 |
| 🔴 高 | PDF 解析 | 自動提取 PDF 中的表格/圖表 |
| 🟡 中 | 地名提取 | 自動識別地名並提取座標 |
| 🟡 中 | 智能優先級 | 根據關鍵詞自動標記優先級 |
| 🟢 低 | 實時監測 | Watch 模式連續監控 raw/ |

---

**最後更新**：2026-04-04 | **系統**：自動化分析管道 v1.0
