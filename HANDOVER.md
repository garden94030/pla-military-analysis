# HANDOVER.md — 交接文件

**最後更新**：2026-04-05 22:30（台北時間 UTC+8）
**本輪執行類型**：人工互動 + Bug 修復
**執行模型**：Claude Sonnet 4.6

---

## 1. 系統當前狀態

| 子系統 | 狀態 | 說明 |
|--------|------|------|
| Gmail 讀取 | ✅ 正常 | token 有效，每日自動刷新 |
| _daily_input | ✅ 已清空 | 今日 18 筆來源已分析並歸檔 |
| _daily_output | ✅ 已產出 | 20260405 綜合報告 + 10 份議題深度分析 |
| wiki/events | ✅ 已同步 | 10+ 筆事件卡片已建立 |
| Git/GitHub | ✅ 最新 | 含今日所有報告與 Bug 修復 |
| Email 通知 | ✅ 正常 | 送完整 HTML 報告，無問題 |
| LINE 通知 | ✅ 已修復 | 現在送完整綜合分析報告純文字（約 2 則訊息） |
| notifier.py | ✅ 已修復 | 兩處 Bug 均已修復（見下方） |
| Windows 排程 | ✅ 運作中 | 每日 05:07 觸發 run_daily_analysis.bat |

---

## 2. 本輪已完成的重大變更

### Bug 修復：notifier.py 兩處問題

**Bug 1：重複發送且內容錯誤**
- 原因：`__main__` 區塊無 `argparse`，`--report`/`--subject` 參數被靜默忽略，改執行硬編碼的舊路徑（`20260331_...`），導致今日分析先寄出舊報告，再寄出正確報告，共兩次
- 修復：加入 `argparse`，支援 `--report` 和 `--subject` 命令列參數；不指定時自動偵測 `_daily_output/` 最新報告
- Commit：`b66a34c`

**Bug 2：LINE 通知只送精簡摘要**
- 原因：`send_report_summary()` 只提取標題＋粗體條列（最多50行），不是完整報告
- 修復：改送完整 `YYYYMMDD_中共軍事動態綜合分析報告.md` 全文，Markdown 語法轉換為純文字（`【】`/`◆`/`▸`），表格分隔行自動略過，超過 5000 字自動分段
- 目前報告約 9000 字 → 分 2 則 LINE 訊息
- Commit：`0cae43a`

### 議題討論：Dispatch 可行性評估

用戶詢問專案是否可 Dispatch。結論：

- **核心限制**：Gmail OAuth token 與所有資料夾均為本機檔案，無法純雲端執行
- **最可行方案**：LINE Bot 指令觸發（在現有 `line_webhook_server.py` 加入 `!立即分析` 指令觸發 `run_daily_analysis.bat`）
- **GitHub Actions**：需先在本機安裝 self-hosted runner，較複雜
- **尚未實作**：等待用戶確認偏好方向

---

## 3. 目前面臨的問題 / 待解決事項

| 優先級 | 問題 | 說明 |
|--------|------|------|
| 🔴 高 | CMSI PDF 未納入分析 | Dr. Erickson CMSI論文（19,999字）已歸檔，待下輪處理 |
| 🟡 中 | Dispatch 方案未實作 | 用戶詢問可行性，尚未決定方向 |
| 🟡 中 | `_daily_output/nul` 遺留檔案 | Windows 路徑問題造成的空檔，可清理 |
| 🟢 低 | 次要議題未建立 wiki 條目 | BAIGUANXINGSHU 反腐、黃海浮標、南海能源等 |

---

## 4. 下一階段發展建議

**優先順序1**：確認 Dispatch 需求方向
- 如要 LINE Bot 指令觸發：修改 `line_webhook_server.py`，加入 `!立即分析` 觸發邏輯
- 如要 GitHub Actions：在本機安裝 `gh-runner`，建立 `.github/workflows/dispatch.yml`

**優先順序2**：處理 CMSI PDF
- `_archive/20260405_052920_CMSI-Conference_PLA_Navy.pdf`
- Dr. Andrew Erickson，The Bridge, Naval War College Foundation, Fall-Winter 2025
- 建立 `wiki/concepts/` 條目（解放軍海軍人員結構分析）

**優先順序3**：清理技術債
- 刪除 `_daily_output/nul` 空檔
- 更新 `wiki/_entities.md` 與 `wiki/.obsidian/workspace.json`（目前有未提交修改）

---

## 附錄：Git Log（最近 6 筆）

```
f321095  feat: LINE Bot 新增 Dispatch 指令 — !立即分析 / !狀態 / !說明
7406179  docs: 更新 HANDOVER.md — notifier Bug修復記錄 + Dispatch評估
0cae43a  feat: LINE 通知改送完整綜合分析報告內容（去除 Markdown 語法）
b66a34c  fix: notifier.py 支援 --report/--subject 參數並自動偵測最新報告
f72ccf2  feat: 20260405 每日自動化分析全面完成 — 10議題+綜合報告+HANDOVER
ec08ae6  feat: 20260405 議題07-10四份深度分析報告全面完成
```

---

## 5. NotebookLM MCP 整合狀態（2026-04-05 新增）

- **安裝版本**：notebooklm-mcp-cli 0.5.16
- **連線帳號**：garden94030@gmail.com
- **MCP 狀態**：`claude mcp list` 顯示 `notebooklm-mcp: ✓ Connected`
- **本地資料夾**：`C:\Users\garde\Documents\NotebookLM\`（slides/infographics/audio/video/docs/sheets/mindmaps/quizzes）
- **筆記本總數**：99 本（owned: 95、shared: 4）
- **已完成功能測試**：建立並刪除測試筆記本，端對端流程正常
