# 🛡️ 20人分析師團隊 — 操作手冊 (Team Operations Manual)

> 版本：v2.0 | 建立：2026-04-04 05:44（台北時間 UTC+8）| 維護：@garden94030

---

## 一、團隊架構總覽

```
┌─────────────────────────────────────────────────────────────┐
│            🛡️ PLA 情報聯合作戰資源中心                      │
│                    (20人虛擬分析師團隊)                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   👤 garde (CIO)   🤖 Antigravity      📡 Claude Code
   首席分析師        後勤自動化           本地分析助理
   最終決策          Grok驅動            深度研析
          │
          ├── 🌊 海洋作戰小組 (navy-01, navy-02)
          ├── ✈️  航空太空小組 (af-01, af-02, space)
          ├── 🚀 火箭網路小組 (rocket-01, rocket-02, cyber)
          ├── 🗺️  台海區域小組 (tw-01, tw-02, ecs, scs-01, scs-02)
          ├── 🔍 情報支援小組 (osint-01, osint-02, lang, tech)
          └── 📊 評估審核小組 (assess, qa)
```

---

## 二、`--dangerously-skip-permissions` 設定說明

### 2.1 設定位置
```json
// .claude/settings.json
{
  "dangerouslySkipPermissions": true,
  "permissions": {
    "allow": ["Bash(*)", "Read(*)", "Write(*)", "Edit(*)", ...]
  }
}
```

### 2.2 使用場景
| 場景 | 指令 | 說明 |
|------|------|------|
| 每日自動化分析 | `claude --dangerously-skip-permissions` | 跳過所有互動確認 |
| 批次派遣子代理人 | `python team/sub_agent_runner.py --daily` | 自動路由 20 名分析師 |
| 單一分析師測試 | `python team/sub_agent_runner.py --analyst analyst-navy-01 --task "..."` | 指定分析師 |

### 2.3 安全注意事項
- ⚠️ 本設定允許 Claude Code 不經確認執行所有工具
- ✅ 適用於本機隔離環境（OneDrive 本地目錄）
- ❌ **不得**在公開伺服器或多人共用環境中使用
- 🔒 .env 中的 API Keys 已加入 .gitignore，不會上傳

---

## 三、子代理人派遣系統

### 3.1 架構說明

```
使用者 → sub_agent_runner.py → team_router.py → 選出最匹配分析師
                              ↓
            讀取 team/profiles/{analyst_id}.CLAUDE.md
                              ↓
            呼叫 claude --dangerously-skip-permissions -p "{task}"
                        --system-prompt-file "{profile}"
                              ↓
            結果寫入 _daily_output/YYYYMMDD_議題XX_*/
```

### 3.2 常用指令

```bash
# 列出所有分析師及配置檔狀態
python team/sub_agent_runner.py --list

# 派遣單一分析師
python team/sub_agent_runner.py \
  --analyst analyst-navy-01 \
  --task "分析今日PLAN艦艇東海巡邏動態"

# 批次派遣（多個關鍵字，自動路由）
python team/sub_agent_runner.py \
  --batch "055驅逐艦南下" "殲20 ADIZ台灣" "火箭軍演習" "南海礁盤建設"

# 每日自動分析（掃描 _daily_input/ 自動分配）
python team/sub_agent_runner.py --daily

# 模擬執行（測試路由邏輯，不實際呼叫 claude）
python team/sub_agent_runner.py --batch "核潛艦" --dry-run

# 指定日期
python team/sub_agent_runner.py --daily --date 20260404
```

### 3.3 並行控制
- 預設最多 **3個** 分析師並行（避免 API rate limit）
- 調整：`--parallel 5`（最多建議 5）
- ThreadPoolExecutor 管理任務佇列，自動等待完成

---

## 四、20人分析師詳細配置

### 4.1 指揮層 (Leadership Layer)

| ID | 職稱 | 主要輸出 | 觸發條件 |
|----|------|---------|---------|
| `garde` | 首席分析師 (CIO) | 跨域合成報告、決策建議 | 戰略、政策、評估、白皮書 |
| `analyst-assess` | 戰略評估官 | 趨勢預測、DIME分析 | 趨勢、前瞻、週報、模擬 |
| `analyst-qa` | 品質管制官 | 格式驗證、事實查核 | 校對、查核、驗證、引用 |

### 4.2 海洋作戰小組

| ID | 職稱 | 主要輸出 | 觸發條件 |
|----|------|---------|---------|
| `analyst-navy-01` | 水面作戰 | 艦隊ORBAT、CSG威脅評估 | 055、航母、驅逐艦、福建艦、艦隊、海軍 |
| `analyst-navy-02` | 水下非對稱 | SSBN巡邏評估、水雷封鎖 | 潛艦、核潛、反潛、水下、聲納、水雷 |

### 4.3 航空太空小組

| ID | 職稱 | 主要輸出 | 觸發條件 |
|----|------|---------|---------|
| `analyst-af-01` | 空優作戰 | ADIZ時序、BVR能力評估 | 殲-20、殲-16、戰機、空軍、ADIZ、空優 |
| `analyst-af-02` | 戰略打擊 | H-6N任務剖面、加油半徑 | 轟炸機、轟-6、加油機、長程打擊 |
| `analyst-space` | 太空安全 | ASAT威脅、北斗精準度 | 衛星、太空、北斗、ASAT、反衛星 |

### 4.4 火箭網路小組

| ID | 職稱 | 主要輸出 | 觸發條件 |
|----|------|---------|---------|
| `analyst-rocket-01` | 核威懾 | 發射井評分、核彈頭推算 | 核彈、核武、彈道飛彈、火箭軍、DF-41 |
| `analyst-rocket-02` | 精準A2AD | 殺傷鏈分析、蒙地卡羅 | 反介入、A2AD、DF-21、DF-26、極音速 |
| `analyst-cyber` | 網路電磁 | ATT&CK TTP矩陣、干擾地圖 | 網路安全、電磁、干擾、APT、資訊戰 |

### 4.5 台海區域小組

| ID | 職稱 | 主要輸出 | 觸發條件 |
|----|------|---------|---------|
| `analyst-tw-01` | 台海戰場 | 登陸演習、RORO船隻追蹤 | 台海、東部戰區、演習、登陸、兩棲 |
| `analyst-tw-02` | 防禦韌性 | 非對稱武器交付、基建RTO | 台灣防禦、非對稱、民防、韌性、關鍵基建 |
| `analyst-ecs` | 東海日本 | 升空統計、宮古通道分析 | 東海、日本、釣魚台、尖閣、自衛隊 |
| `analyst-scs-01` | 南海主權 | 礁盤評分卡、菲中指數 | 南海、仁愛礁、黃岩島、菲律賓、南沙 |
| `analyst-scs-02` | 灰色地帶 | 升級量表、民兵識別 | 灰色地帶、海警、民兵、水砲、法律戰 |

### 4.6 情報支援小組

| ID | 職稱 | 主要輸出 | 觸發條件 |
|----|------|---------|---------|
| `analyst-osint-01` | IMINT影像 | 衛星標注、KML輸出 | 衛星影像、Maxar、Planet、基地、照片 |
| `analyst-osint-02` | OSINT開源 | 輿情追蹤、採購逆向 | X平台、追蹤、數據、輿情、招標 |
| `analyst-lang` | 語言政工 | 術語解讀、黨文件分析 | 解放軍報、文件、術語、政治部、黨委 |
| `analyst-tech` | 軍工技術 | TRL評分、AI算力估算 | AI、智能化、無人機、晶片、軍民融合 |

---

## 五、分析師 System Prompt 摘要

> 完整配置見 `team/profiles/{analyst_id}.CLAUDE.md`

| 分析師 | 核心 Prompt 方向 |
|--------|----------------|
| garde | 30年軍研 CIO，體系作戰全域研判，ACH分析法，NET評估框架 |
| navy-01 | PLAN藍海轉型，CSG側翼威脅，AIS/衛星雙軌追蹤，ORBAT分析 |
| navy-02 | SSBN核威懾巡航，靜音技術評估，水下封鎖建模 |
| af-01 | 智能化空戰，BVR超視距，ADIZ侵擾時序統計分析 |
| af-02 | 遠程轟炸，第二島鏈突破，空中補給鏈韌性評估 |
| rocket-01 | NFU政策轉變偵測，發射井衛星進度評分，核彈頭數量推算 |
| rocket-02 | 航母殺手殺傷鏈，A2AD飽和攻擊蒙地卡羅模擬 |
| cyber | 制資訊權，MITRE ATT&CK PLA TTP，C2破壞威脅分析 |
| space | 北斗精準度分析，ASAT高度包絡，RPO異常偵測 |
| tw-01 | 聯合登陸演練，RORO/氣墊船集結，適登海灘GIS |
| tw-02 | 混合戰複合影響，基礎設施RTO，武器交付甘特圖 |
| ecs | 日本防衛與PLA互動，ARIMA升空預測，宮古通道分析 |
| scs-01 | 礁盤軍事化評分卡，菲中事件升級指數，FONOP法律分析 |
| scs-02 | 灰色地帶10級量表，CCG行動解讀，民兵識別三合一 |
| osint-01 | IMINT標注規範，變化偵測，KML地理輸出 |
| osint-02 | OSINT ABCD可信度評級，ADS-B/AIS，採購逆向分析 |
| lang | 解放軍報TF-IDF，中共術語解碼，政工制度分析 |
| tech | TRL技術成熟度，AI算力庫存估算，晶片禁令影響 |
| assess | 軍力指數計算，DIME框架，2027/2035目標評估 |
| qa | 三層驗證法，偏差篩查矩陣，Chicago格式自動驗證 |

---

## 六、工作流程

### 6.1 每日標準流程

```
06:00  ──► gmail_reader.py 讀取郵件 → _daily_input/
06:05  ──► sub_agent_runner.py --daily 批次派遣
              │
              ├─► analyst-navy-01 (PLAN艦艇議題)
              ├─► analyst-af-01 (空軍議題)
              ├─► analyst-rocket-02 (A2AD議題)
              └─► ...依關鍵字路由
              │
06:30  ──► briefing_generator.py 合併報告
06:35  ──► notifier.py 推播 Email + LINE
06:40  ──► git commit + push
```

### 6.2 臨時任務流程

```
分析師收到即時情報
      │
      ▼
拖入 _daily_input/ 或直接下指令
      │
      ▼
python team/sub_agent_runner.py \
  --analyst [最適分析師] \
  --task "分析任務描述"
      │
      ▼
報告輸出至 _daily_output/
      │
      ▼
analyst-qa 審核 → GitHub PR → merge → wiki/
```

### 6.3 PR 審核流程

```
1. 分析師完成報告 → git add + commit (branch: analyst-YYYYMMDD-*)
2. 建立 PR → 自動指派 @analyst-qa 審核
3. QA 審核：引用格式、數據驗證、偏差篩查
4. 首席 @garde 最終核可 → merge to main
5. wiki_compiler.py 自動更新 wiki/_index.md
```

---

## 七、故障排除

### 7.1 claude 指令找不到

```
❌ 錯誤：FileNotFoundError: claude not found
✅ 解法：確認 Claude Code CLI 已安裝
   npm install -g @anthropic-ai/claude-code
   或確認 PATH 包含 claude.exe 所在目錄
```

### 7.2 分析師配置檔不存在

```
❌ 錯誤：找不到子代理人配置檔：team/profiles/analyst-xx.CLAUDE.md
✅ 解法：重新生成配置檔
   # 手動建立或執行初始化
   python team/sub_agent_runner.py --list  # 確認哪些缺少配置檔
```

### 7.3 API Rate Limit

```
❌ 症狀：多個子代理人同時執行導致 API 超限
✅ 解法：降低並行數
   python team/sub_agent_runner.py --daily --parallel 2
```

### 7.4 Windows 編碼問題

```
❌ 錯誤：UnicodeDecodeError 或 ??? 亂碼
✅ 解法：已在 sub_agent_runner.py 設定 sys.stdout.reconfigure(encoding='utf-8')
   確認 Python 版本 >= 3.9
```

---

## 八、版本記錄

| 版本 | 日期 | 變更 |
|------|------|------|
| v1.0 | 2026-04-03 | 初始建立 analysts.json + team_router.py |
| v1.5 | 2026-04-03 | 新增 briefing_generator.py |
| v2.0 | 2026-04-04 | 新增 sub_agent_runner.py、20個 profile.CLAUDE.md、dangerouslySkipPermissions |

---

*本操作手冊由自動化系統生成 | 最後更新：2026-04-04 05:44（台北時間 UTC+8）*
