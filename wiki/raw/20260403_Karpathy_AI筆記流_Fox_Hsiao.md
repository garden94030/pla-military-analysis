---
title: "AI 大神 Karpathy 的 AI 筆記流，一般人也能做到八成"
source: Fox Hsiao — 2026-04-03
url: https://medium.com/@foxhsiao (原文連結)
type: methodology-reference
relevance: 本系統架構高度吻合此方法論（raw/ → wiki/ → AI查詢）
tags: [AI工作流, 知識管理, Karpathy, Obsidian, RAG]
saved_date: 2026-04-03
---

> [!note] 系統關聯性
> 本文描述的 Karpathy 知識庫架構與本專案現有架構幾乎完全對應：
> - `raw/` = Karpathy 的 raw/ 原始資料夾
> - `wiki/concepts/` + `wiki/events/` = 自動編譯的百科全書
> - `wiki_compiler.py` = Karpathy 提到的「自動整理 AI 腳本」
> - `wiki_health.py` = 第五步「定期健康檢查」
> - `wiki_query.py` = 第三步「對知識庫提問」

---

## 原文摘錄

**作者**：Fox Hsiao｜**日期**：2026-04-03｜**閱讀時間**：12 分鐘

### 核心概念：把 AI 從便利商店變成圖書館

大部分人用 ChatGPT 的方式是「實習生 A」：每次開新對話，之前聊過的東西全部消失。
Karpathy 做的是「實習生 B」：每次回答後整理成筆記，越回答越快、越精準。

---

### Karpathy 六步驟系統

**第一步：把資料全部丟進 raw/ 資料夾**
- 工具：Obsidian Web Clipper（一鍵存成本地 Markdown 檔）
- 原則：不管格式亂不亂，先存再說

**第二步：叫 AI 把原始資料「編譯」成百科全書**
- AI 自動寫摘要、分類、建立跨主題連結
- 使用者只負責丟新資料，AI 負責維護知識體系
- **重要**：原始筆記（raw/）與 AI 產出的 wiki 應分開存放

**第三步：直接對百科全書提問**
- 知識庫達 100 篇/40 萬字規模後，直接對 AI 提問
- Karpathy 發現不需額外 RAG 系統，AI 自己的索引已足夠

**第四步：輸出多種格式**
- Markdown 筆記、Marp 簡報、matplotlib 圖表
- **關鍵**：查詢結果「回存」到知識庫 → 越用越厚

**第五步：定期健康檢查**
- AI 掃描全庫，找矛盾、補缺漏、發現跨主題關聯

**第六步：vibe coding 做搜尋工具**
- 用嘴巴告訴 AI 要什麼功能，AI 幫你寫程式

---

### Lex Fridman 的兩個進階玩法

1. **互動式 HTML 儀表板**：不是靜態圖表，而是可點、可篩、可拖的網頁
2. **跑步時語音學習**：把精華版 wiki 載入語音模式，邊跑步邊提問（互動式 Podcast）

---

### 一般人三步驟版本（不需寫程式）

1. **建立原始資料庫**：Obsidian 或 Notion，裝 Web Clipper，看到東西先存
2. **定期讓 AI 消化**：每週把原始資料丟給 ChatGPT/Claude，用結構化提示整理
3. **對知識庫提問**：開新對話時先貼 wiki 當背景，再問問題

**現成工具推薦**：Google NotebookLM（最接近這套概念的免費工具）

---

### 關鍵引述

> Karpathy：「這整套流程應該變成一個正式的產品，而不只是一堆拼湊的腳本。」

---

### 原始資料連結

- Andrej Karpathy 原始推文：LLM Knowledge Bases
- Lex Fridman 回覆：Similar setup with voice-mode learning
- Obsidian 官方網站：https://obsidian.md（免費）
