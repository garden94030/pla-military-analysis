# 📋 PLA 情報系統 Task Board
> 最後更新：2026-04-04 | GitHub: `garden94030/pla-military-analysis`

---

## ✅ 已完成 (Completed)

### 基礎建設
- [x] `analysis.py` 核心分析引擎（Claude/Grok 雙後端）
- [x] `wiki_compiler.py` 知識庫自動編譯（`--team-sync` 發 PR）
- [x] `wiki_health.py` 健康監控（PR/stale/queue/reviewer 動態輪派）
- [x] `notifier.py` LINE + Email 通知
- [x] `啟動LINE接收器.py` v2（自動偵測 Cloudflare URL + 更新 LINE API）
- [x] `wiki_query.py` 知識庫查詢介面

### Token 優化
- [x] wiki context：400字/塊 × 5塊（原800×8），省約 40-55%
- [x] `max_tokens`：3000（原4000）
- [x] SKILL 深度分析：7章（原10-12章）

### 自動交接系統
- [x] `handover_check.py` Stop/PreCompact hook 觸發器
- [x] `.claude/settings.json` Stop + PreCompact 雙重 hooks
- [x] `CLAUDE.md` 強制規則（每輪必須撰寫 HANDOVER.md）

### 虛擬 20 人分析師團隊
- [x] `team/analysts.json`：20名角色（含 CSIS 專家級 system_prompt）
- [x] `team/team_router.py`：關鍵字→分析師自動路由
- [x] `team/ROSTER.md`：可視化團隊名錄
- [x] `wiki_health.py` 動態載入 20 人 TEAM_REVIEWERS

### GIS / KML 地理情報系統
- [x] `analysis.py` KML 生成功能（`generate_kml_file`）
- [x] 非洲飄移 (0,0) Bug 修復（None 座標處理）
- [x] `_geo_output/` 統一備份目錄
- [x] `_system/issue_counter.json` 全域議題編號管理

### Grok API / Python 3.13 修復
- [x] 解決 `openai` import 錯誤
- [x] 修正 `.docx` 中文檔名/權限錯誤

### 專家複審機制 (Agentic Review)
- [x] `get_expert_review()` 函數（依路由結果呼叫對應分析師 system_prompt）
- [x] 報告自動附帶「專家評核意見」與「戰略風險等級」

### 知識庫 Skills（`~/.claude/skills/`）
- [x] `/daily-analysis`：每日分析觸發
- [x] `/intel-health`：健康報告
- [x] `/intel-weekly`：週報生成

### 已產出成果（2026-04-03）
- [x] 議題 02-10：9份個別分析報告（_daily_output/）
- [x] 議題 11：綜合分析報告（中國核武現代化擴建）
- [x] `wiki/assessments/2026W14_週報.md`：第一份正式週報 ✅
- [x] `_geo_output/` 3份 KML 地理動態圖資

---

## ⏭️ 待辦 (Backlog)

### 🔴 高優先
- [ ] `analysis.py` 新功能完整執行測試（GIS + 專家複審 + wiki/raw 掃描）
- [ ] `_system/handover_check.py` 舊副本刪除

### 🟡 中優先
- [ ] `wiki_compiler.py --team-sync` PR 流程完整測試
- [ ] LINE Webhook Task Scheduler（每天早上自動啟動）

### 🟢 低優先
- [ ] `wiki_query.py` Flask 前端網頁介面
- [ ] `_geo_output/` Google Earth 即時同步設定

---

## 🐛 已知問題

| 問題 | 解法 |
|------|------|
| `git index.lock` 衝突 | `powershell -Command "Remove-Item '.git\index.lock' -Force; git add .; git commit -m '...'; git push"` |
| Windows cp950 編碼錯誤 | 腳本頂部加 `sys.stdout.reconfigure(encoding="utf-8")` |
| Obsidian Web Clipper 斜線檔名 | 手動改 `/`→`-`，或 `{{title \| replace("/","-")}}` |
