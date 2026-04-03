# ✅ Obsidian Raw 自動化解決方案 - 完整交付

## 📌 問題回顧

| 問題 | 表現 | 根本原因 |
|------|------|--------|
| **重疊** | raw/ 與 _daily_input/ 職責不清 | 無明確劃分 |
| **無自動化** | raw/ 新檔案無自動觸發 | 缺乏監測機制 |
| **流程斷裂** | Obsidian → raw/ → ??? | 沒有自動橋接 |

---

## 🎯 解決方案架構

### 新的完整流程

```
Obsidian Web Clipper
    ↓ (自動保存)
wiki/raw/
    ↓ (PostToolUse Hook 監測)
auto_analyze_raw.py
    ↓ (掃描 + 轉移)
_daily_input/auto_*.md
    ↓ (標記 pending)
/daily-analysis skill
    ↓ (執行分析)
_daily_output/ (分析報告)
```

---

## 📦 已交付元件

### 1️⃣ auto_analyze_raw.py（新建）
**位置**：`/auto_analyze_raw.py`
**功能**：
- ✅ 掃描 `wiki/raw/` 新檔案
- ✅ 自動生成分析任務卡到 `_daily_input/`
- ✅ 維護已處理檔案日誌
- ✅ 支援圖片/PDF/文件檔案格式

**使用方式**：
```bash
python auto_analyze_raw.py                    # 手動掃描
python auto_analyze_raw.py --process-file <path>  # 單檔處理
```

### 2️⃣ raw_processed.json（新建）
**位置**：`/_system/raw_processed.json`
**作用**：
- ✅ 記錄已處理檔案
- ✅ 防止重複轉移
- ✅ 追蹤處理歷史

### 3️⃣ PostToolUse Hook（已配置）
**位置**：`.claude/settings.json`
**觸發**：每次 Write/Edit 完成
**動作**：
- ✅ 自動執行 `auto_analyze_raw.py`
- ✅ 背景非阻塞執行
- ✅ 無需手動干預

### 4️⃣ RAW_AUTOMATION_GUIDE.md（新建）
**位置**：`/RAW_AUTOMATION_GUIDE.md`
**包含**：
- ✅ 完整使用說明
- ✅ 故障排除指南
- ✅ 最佳實踐建議
- ✅ 監控命令

---

## 🔄 職責明確化

### 🎞️ wiki/raw/ — 「黑洞」倾倒區
```
目的：無腦接收（Obsidian Web Clipper）
內容：
  ├─ 網頁截圖
  ├─ PDF 文件
  ├─ 長截圖
  └─ 原始資料（未經篩選）
  
管理：自動化系統
  └─ auto_analyze_raw.py 監控
     └─ 新檔案自動轉移
```

### 📋 _daily_input/ — 分析待列隊
```
目的：準備分析（人工審視）
內容：
  ├─ auto_*.md （自動生成任務卡）
  ├─ 手工建立的分析議題
  └─ 標記優先級的項目
  
狀態：pending → in_progress → completed
管理：人工 + 自動化 skill
  └─ /daily-analysis 執行分析
```

---

## 🚀 操作流程（實際使用）

### 場景 A：用 Obsidian Web Clipper

1. **配置 Clipper**（一次性）
   ```
   儲存路徑：wiki/raw/
   檔案名稱：{{title | replace("/", "-")}}
   ```

2. **使用**（每次）
   ```
   網頁截圖 → Obsidian Web Clipper 按鈕
          ↓ (自動保存到 wiki/raw/)
   等待系統自動處理...
          ↓ (PostToolUse Hook 觸發)
   任務卡自動出現在 _daily_input/auto_*.md
          ↓ (查看並調整優先級)
   執行 /daily-analysis 進行分析
   ```

3. **執行分析**
   ```bash
   # 方式 1：使用 skill
   /daily-analysis
   
   # 方式 2：手動執行
   python analysis.py
   ```

### 場景 B：手動觸發檢查

```bash
# 立即掃描 raw/ 並轉移新檔案
python auto_analyze_raw.py

# 查看處理狀態
python auto_analyze_raw.py  # 輸出狀態報告

# 檢查已處理檔案清單
cat _system/raw_processed.json | jq .
```

---

## ✨ 關鍵改進對比

| 層面 | 改進前 | 改進後 |
|------|--------|--------|
| **raw/ 職責** | 模糊（與 _daily_input/ 重疊） | 明確（黑洞倾倒區） |
| **自動化** | 無（手工移檔） | 有（自動監測 + 轉移） |
| **流程** | 斷裂（Obsidian → raw/ → 卡住） | 完整（raw/ → 任務卡 → 分析） |
| **去重** | 無（可能重複處理） | 有（processed.json 追蹤） |
| **可靠性** | 易遺漏檔案 | 自動不遺漏 |

---

## 🔧 配置確認清單

- [x] `auto_analyze_raw.py` 已建立（175 行代碼）
- [x] `raw_processed.json` 已初始化
- [x] `.claude/settings.json` 已添加 PostToolUse Hook
- [x] `RAW_AUTOMATION_GUIDE.md` 完整文檔已建立
- [x] 職責劃分已明確化
- [x] 故障排除指南已準備

---

## 📝 後續推薦

### 🟡 中優先（本週）
1. **測試流程**
   ```bash
   # 1. 將測試圖片放入 wiki/raw/
   # 2. 執行自動化
   python auto_analyze_raw.py
   # 3. 驗證 _daily_input/ 中是否出現任務卡
   ```

2. **驗證 Hook**
   - 在專案中做任何 Write/Edit
   - 觀察 PostToolUse Hook 是否自動執行
   - 確認 raw/ 新檔案自動轉移

### 🔴 高優先（本月）
3. **完整測試流程**
   - Obsidian → raw/ → auto_analyze_raw.py → _daily_input/
   - → /daily-analysis → _daily_output/
   - 驗證端到端工作

4. **優化**
   - 調整任務卡模板（如需要）
   - 新增特定關鍵詞快速路由
   - 完善優先級判斷邏輯

---

## 🎓 核心概念

**三層自動化**：
```
第1層 - 收集：Obsidian Web Clipper → raw/
第2層 - 轉移：PostToolUse Hook → auto_analyze_raw.py
第3層 - 分析：/daily-analysis Skill → _daily_output/
```

**避免重複**：
```
raw_processed.json
    ↓
防止同檔案多次轉移
    ↓
幂等性保證
```

---

## 🆘 快速故障排除

| 症狀 | 診斷 | 解決 |
|------|------|------|
| raw/ 檔案未轉移 | `auto_analyze_raw.py` 未執行 | `python auto_analyze_raw.py` |
| 同檔案重複轉移 | raw_processed.json 損壞 | 重置處理日誌 |
| Hook 未觸發 | settings.json 配置錯誤 | 檢查 PostToolUse 語法 |
| 檔案格式不支援 | 副檔名不在白名單 | 修改 `is_image_or_document()` |

---

## 📊 成果驗證指標

✅ **自動化達成**：
- [ ] raw/ 新檔案自動轉移到 _daily_input/
- [ ] 無需手動複製檔案
- [ ] 職責清晰無重疊
- [ ] Hook 背景自動運作

✅ **流程完整**：
- [ ] Obsidian → raw/（自動）
- [ ] raw/ → 任務卡（自動）
- [ ] 任務卡 → 分析（手動觸發）
- [ ] 分析 → 報告（自動生成）

---

**系統版本**：1.0 | **日期**：2026-04-04 | **狀態**：✅ 就緒部署
