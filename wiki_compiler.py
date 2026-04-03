"""
wiki_compiler.py — 情報知識庫編譯器

功能：
1. 從 _daily_output/ 的既有分析報告中，萃取概念與事件
2. 自動建立 wiki/concepts/ 和 wiki/events/ 文章
3. 維護 wiki/_index.md、_timeline.md、_entities.md

用法：
  python wiki_compiler.py                  # 回填所有既有報告
  python wiki_compiler.py --date 20260403  # 只處理特定日期
  python wiki_compiler.py --latest         # 只處理最新一份報告
"""

import os
import sys
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from team.team_router import route_topic

sys.stdout.reconfigure(encoding='utf-8')

# ============= 路徑設定 =============
WORKSPACE = Path(r"C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新")
OUTPUT_DIR = WORKSPACE / "_daily_output"
WIKI_DIR = WORKSPACE / "wiki"
CONCEPTS_DIR = WIKI_DIR / "concepts"
EVENTS_DIR = WIKI_DIR / "events"
ASSESSMENTS_DIR = WIKI_DIR / "assessments"
ENV_FILE = WORKSPACE / ".env"

# 確保目錄存在
for d in [WIKI_DIR, CONCEPTS_DIR, EVENTS_DIR, ASSESSMENTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ============= 環境設定 =============
def _load_env() -> dict:
    config = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                config[k.strip()] = v.strip()
    return config

_cfg = _load_env()
GROK_KEY = _cfg.get("GROK_API_KEY") or os.environ.get("GROK_API_KEY", "")
ANTHROPIC_KEY = _cfg.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")


def get_llm_client():
    """取得 LLM 客戶端"""
    # 遵循要求：系統自動化腳本預設使用 Grok
    if GROK_KEY:
        from openai import OpenAI
        return "grok", OpenAI(api_key=GROK_KEY, base_url="https://api.x.ai/v1")
    elif ANTHROPIC_KEY:
        import anthropic
        return "anthropic", anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    else:
        print("❌ 沒有可用的 API Key")
        sys.exit(1)


def llm_call(prompt: str, system: str = "", max_tokens: int = 3000) -> str:
    """統一的 LLM 呼叫介面"""
    backend, client = get_llm_client()
    if backend == "anthropic":
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system or "你是知識庫編譯助手。",
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    else:
        resp = client.chat.completions.create(
            model="grok-3",
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system or "你是知識庫編譯助手。"},
                {"role": "user", "content": prompt}
            ]
        )
        return resp.choices[0].message.content


# ============= 掃描既有議題 =============
def scan_issue_folders() -> list:
    """掃描 _daily_output/ 下的所有議題資料夾"""
    issues = []
    for item in sorted(OUTPUT_DIR.iterdir()):
        if item.is_dir() and item.name.startswith("2026"):
            # 格式：20260403_議題01_解放軍海軍日本海行動與第一島鏈突破
            match = re.match(r"(\d{8})_議題(\d+)_(.+)", item.name)
            if match:
                date_str, issue_num, title = match.groups()
                # 找到裡面的 .md 檔案
                md_files = list(item.glob("*.md"))
                if md_files:
                    issues.append({
                        "date": date_str,
                        "number": issue_num,
                        "title": title,
                        "folder": item,
                        "md_file": md_files[0],
                    })
    return issues


def scan_daily_reports() -> list:
    """掃描 _daily_output/ 下的綜合分析報告"""
    reports = []
    for f in sorted(OUTPUT_DIR.glob("*中共軍事動態綜合分析報告.md")):
        match = re.match(r"(\d{8})_", f.name)
        if match:
            reports.append({
                "date": match.group(1),
                "file": f,
            })
    return reports


# ============= 知識編譯 =============
def compile_event(issue: dict) -> Path:
    """從議題資料夾建立事件卡片"""
    content = issue["md_file"].read_text(encoding="utf-8")
    date_str = issue["date"]
    title = issue["title"]
    
    # 清理檔名中的非法字元
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
    event_file = EVENTS_DIR / f"{date_str}_{safe_title}.md"
    
    if event_file.exists():
        return event_file  # 已存在，跳過
    
    analyst = route_topic(title)
    
    # 建立事件卡片（直接用原始分析內容，加上 frontmatter）
    card = f"""---
date: {date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}
title: {title}
type: event
tags: [事件, {date_str}]
author: Antigravity-Compiler
reviewer: @{analyst['github']} ({analyst['name']})
---

# {title}

**日期**：{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}
**來源議題**：{issue['folder'].name}

---

{content}
"""
    event_file.write_text(card, encoding="utf-8")
    return event_file


def extract_concepts_from_issues(issues: list) -> dict:
    """從所有議題中提取概念關鍵字並歸類"""
    # 預定義的概念清單（基於你已有的 107 個議題）
    concept_keywords = {
        "055型驅逐艦": ["055", "仁海級", "驅逐艦", "東莞", "安慶", "拉薩", "鞍山"],
        "台海灰色地帶作戰": ["灰色地帶", "海警", "海纜", "AIS", "漁船"],
        "東沙群島防禦": ["東沙", "Pratas", "南海前哨"],
        "解放軍反腐清洗": ["反腐", "清洗", "院士", "楊偉", "譚瑞松"],
        "海纜安全與通訊韌性": ["海纜", "海底電纜", "宏泰", "斷網"],
        "殲6無人機飽和攻擊": ["殲6", "殲-6", "J-6", "無人自殺", "飽和攻擊"],
        "解放軍海軍現代化": ["052D", "054B", "護衛艦", "航母", "艦隊"],
        "台灣國防預算": ["國防預算", "軍購", "HIMARS", "標槍", "特別預算"],
        "美伊衝突與印太影響": ["怒火行動", "伊朗", "荷姆茲", "Epic Fury"],
        "中國AI與軍民融合": ["人工智慧", "AI", "軍民融合", "十五規劃"],
        "南海海警巡邏": ["黃岩島", "薩賓娜", "CCG", "海警船", "南海巡邏"],
        "中國海底監測網路": ["海底感測器", "向陽紅", "浮標", "UUV", "水下無人"],
        "台海軍機活動監測": ["ADIZ", "防空識別區", "軍機", "架次", "越中線"],
        "日本防衛與對中策略": ["對馬海峽", "日本海", "JMSDF", "與那國", "先島群島"],
        "安洵公司網路戰": ["安洵", "i-Soon", "78012", "網路戰", "黑客"],
    }
    
    # 為每個概念收集相關事件
    concept_events = {k: [] for k in concept_keywords}
    
    for issue in issues:
        content = ""
        try:
            content = issue["md_file"].read_text(encoding="utf-8")
        except:
            continue
        
        combined = issue["title"] + " " + content[:2000]
        
        for concept, keywords in concept_keywords.items():
            if any(kw in combined for kw in keywords):
                concept_events[concept].append(issue)
    
    return concept_events


def compile_concept(concept_name: str, related_issues: list) -> Path:
    """為一個概念建立或更新 wiki 文章"""
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', concept_name)
    concept_file = CONCEPTS_DIR / f"{safe_name}.md"
    
    if concept_file.exists():
        return concept_file  # 第一輪回填不覆蓋
    
    # 收集相關事件的摘要
    event_refs = []
    for issue in related_issues[:15]:  # 最多 15 個
        date = f"{issue['date'][:4]}-{issue['date'][4:6]}-{issue['date'][6:8]}"
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', issue['title'])
        event_refs.append(f"- {date}：[[{issue['date']}_{safe_title}|{issue['title']}]]")
    
    events_section = "\n".join(event_refs) if event_refs else "- 尚無記錄"
    
    analyst = route_topic(concept_name)
    
    # 團隊版 Frontmatter
    card = f"""---
title: {concept_name}
type: concept
status: draft
author: Antigravity-Compiler
reviewer: @{analyst['github']} ({analyst['name']})
created: {datetime.now().strftime('%Y-%m-%d')}
updated: {datetime.now().strftime('%Y-%m-%d')}
tags: [概念]
---

# {concept_name}

> [!summary]
> 此文章由知識庫編譯器自動建立，整合了所有與「{concept_name}」相關的情資事件。

## 概述

（待 LLM 深化撰寫）

## 相關事件時間線

{events_section}

## 關鍵指標與數據

（待更新）

## 對台灣安全的影響評估

（待更新）

## 延伸閱讀

（待補充）
"""
    concept_file.write_text(card, encoding="utf-8")
    return concept_file

def push_pr_for_topic(concept_name: str, files_to_commit: list):
    """為單一主題的更新，開啟新的分支並發送 GitHub Pull Request"""
    safe_name = re.sub(r'[<>:"/\\|?*]', '-', concept_name).replace(" ", "")
    date_str = datetime.now().strftime('%Y%m%d%H%M')
    branch_name = f"auto-intel/{date_str}-{safe_name}"
    
    try:
        # 切換回主分支並確保乾淨
        subprocess.run(["git", "checkout", "main"], cwd=WORKSPACE, capture_output=True, encoding='utf-8', errors='ignore')
        # 建立新分支
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=WORKSPACE, check=True, capture_output=True, encoding='utf-8', errors='ignore')
        
        # 加入檔案
        for f in files_to_commit:
            subprocess.run(["git", "add", str(f)], cwd=WORKSPACE, check=True, capture_output=True, encoding='utf-8', errors='ignore')
        
        # 準備 Commit 和 Push
        commit_msg = f"update(wiki): AI 更新情報報告 [{concept_name}]"
        res = subprocess.run(["git", "commit", "-m", commit_msg], cwd=WORKSPACE, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        # 若沒有變更就不需要發 PR
        if "nothing to commit" in res.stdout:
            subprocess.run(["git", "checkout", "main"], cwd=WORKSPACE, capture_output=True, encoding='utf-8', errors='ignore')
            return

        subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=WORKSPACE, check=True, capture_output=True, encoding='utf-8', errors='ignore')
        
        # 建立 PR 並自動指派負責人
        pr_title = f"🚨 自動編譯情報更新：[ {concept_name} ]"
        analyst = route_topic(concept_name)
        assignee = analyst['github']
        pr_body = f"Antigravity AI 已根據今日情資建立/更新了 **{concept_name}** 相關情報。\n\n請對應小組分析師 **@{assignee}** ({analyst['name']}) 進行 Review 並 Merge 本次更新。"
        
        # 使用 gh pr create --assignee 指派負責人
        subprocess.run(["gh", "pr", "create", "--title", pr_title, "--body", pr_body, "--assignee", assignee], cwd=WORKSPACE, check=True, capture_output=True, encoding='utf-8', errors='ignore')
        
        print(f"   🚀 已成功為 {concept_name} 自動發送 Pull Request (指派給: @{assignee})")
    except Exception as e:
        print(f"   ⚠️ 建立 PR 發生錯誤 ({concept_name}): {e}")
    finally:
        subprocess.run(["git", "checkout", "main"], cwd=WORKSPACE, capture_output=True, encoding='utf-8', errors='ignore')


def build_index(issues: list, concepts: dict):
    """建立全域索引 _index.md"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 概念索引
    concept_lines = []
    for name in sorted(concepts.keys()):
        count = len(concepts[name])
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
        concept_lines.append(f"| [[{safe_name}\\|{name}]] | {count} 則相關事件 |")
    
    concept_table = "\n".join(concept_lines)
    
    # 事件索引（按日期分組）
    events_by_date = {}
    for issue in issues:
        d = issue["date"]
        if d not in events_by_date:
            events_by_date[d] = []
        events_by_date[d].append(issue)
    
    event_sections = []
    for date in sorted(events_by_date.keys(), reverse=True)[:14]:  # 最近 14 天
        formatted = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        event_sections.append(f"\n### {formatted}\n")
        for issue in events_by_date[date]:
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', issue['title'])
            event_sections.append(f"- [[{issue['date']}_{safe_title}|{issue['title']}]]")
    
    events_text = "\n".join(event_sections)
    
    index = f"""---
title: 知識庫索引
updated: {now}
---

# 🔍 中共軍事動態情報知識庫

> **最後更新**：{now}
> **概念文章**：{len(concepts)} 篇
> **事件卡片**：{len(issues)} 則
> **涵蓋日期**：2026-03-18 至今

---

## 📌 概念文章索引

| 概念 | 關聯事件數 |
|------|-----------|
{concept_table}

---

## 📅 事件時間線（近兩週）

{events_text}

---

## 🗂️ 資料夾導覽

- [[_timeline|完整時間線]]
- [[_entities|實體名錄]]
- `concepts/` — 跨時間的主題性知識文章
- `events/` — 具體事件卡片
- `assessments/` — 週報與趨勢評估
"""
    (WIKI_DIR / "_index.md").write_text(index, encoding="utf-8")


def build_timeline(issues: list):
    """建立時間線"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    lines = [f"""---
title: 事件時間線
updated: {now}
---

# 📅 中共軍事動態事件時間線

"""]
    
    events_by_date = {}
    for issue in issues:
        d = issue["date"]
        if d not in events_by_date:
            events_by_date[d] = []
        events_by_date[d].append(issue)
    
    for date in sorted(events_by_date.keys(), reverse=True):
        formatted = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        lines.append(f"\n## {formatted}\n")
        for issue in events_by_date[date]:
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', issue['title'])
            lines.append(f"- 議題{issue['number']}：[[{issue['date']}_{safe_title}|{issue['title']}]]")
    
    (WIKI_DIR / "_timeline.md").write_text("\n".join(lines), encoding="utf-8")


def build_entities(issues: list):
    """建立實體名錄"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    entities_text = f"""---
title: 實體名錄
updated: {now}
---

# 🏛️ 實體名錄

## 解放軍艦艇

| 艦名 | 型號 | 舷號 | 所屬戰區 | 相關概念 |
|------|------|------|---------|---------|
| 拉薩 | 055型 | 102 | 北方戰區 | [[055型驅逐艦]] |
| 東莞 | 055型 | 109 | 東部戰區 | [[055型驅逐艦]] |
| 安慶 | 055型 | 110 | 東部戰區 | [[055型驅逐艦]] |
| 鞍山 | 055型 | — | 北方戰區 | [[055型驅逐艦]] |
| 貴陽 | 052D型 | 119 | 北方戰區 | [[解放軍海軍現代化]] |
| 成都 | 052D型 | 120 | 北方戰區 | [[解放軍海軍現代化]] |
| 可可西里湖 | 903A型 | 903 | 北方戰區 | [[解放軍海軍現代化]] |

## 解放軍關鍵人物

| 姓名 | 身分 | 狀態 | 相關概念 |
|------|------|------|---------|
| 楊偉 | 殲-20 總設計師 | 失蹤逾一年 | [[解放軍反腐清洗]] |
| 譚瑞松 | 前中航工業董事長 | 死緩 | [[解放軍反腐清洗]] |
| 吳曼青 | 院士（雷達/電子戰） | 除名 | [[解放軍反腐清洗]] |
| 趙憲庚 | 院士（核工程） | 除名 | [[解放軍反腐清洗]] |
| 魏毅寅 | 院士（飛彈/航天） | 除名 | [[解放軍反腐清洗]] |

## 情報來源機構

| 來源 | 類型 | 頻率 |
|------|------|------|
| Tom Shugart (Substack) | OSINT/軍事分析 | 每日 |
| CCA PLA Watch (Asia Society) | 智庫 | 不定期 |
| AMTI (CSIS) | 衛星/AIS分析 | 不定期 |
| INDSR 國防研究院 | 官方智庫 | 每週 |
| Futura Doctrina (Mick Ryan) | 軍事評論 | 每日 |
| Grok 每日彙整 (x.ai) | AI 摘要 | 每日 |

## 關鍵地理位置

| 地點 | 座標/區域 | 重要性 | 相關概念 |
|------|----------|--------|---------|
| 東沙群島 | 南海北端 | 台灣前哨 | [[東沙群島防禦]] |
| 對馬海峽 | 日韓之間 | 第一島鏈突破口 | [[日本防衛與對中策略]] |
| 黃岩島 | 南海 | 中菲爭議 | [[南海海警巡邏]] |
| 尖閣諸島 | 東海 | 日中爭議 | [[中國海底監測網路]] |
| 東引 | 馬祖 | 海纜節點 | [[海纜安全與通訊韌性]] |
"""
    (WIKI_DIR / "_entities.md").write_text(entities_text, encoding="utf-8")


# ============= 主程序 =============
def main():
    print("=" * 60)
    print("  📚 中共軍事動態情報知識庫 — 知識編譯器")
    print("=" * 60)
    
    # Step 1: 掃描既有議題
    print("\n🔍 掃描既有議題資料夾...")
    issues = scan_issue_folders()
    print(f"   找到 {len(issues)} 個議題資料夾")
    
    # Step 2: 建立事件卡片
    print("\n📝 建立事件卡片...")
    created_events = 0
    for issue in issues:
        try:
            event_file = compile_event(issue)
            if event_file:
                created_events += 1
        except Exception as e:
            print(f"   ⚠️ 跳過 {issue['title']}: {e}")
    print(f"   ✅ 完成 {created_events} 張事件卡片")
    
    # Step 3: 提取概念並建立文章
    print("\n🧠 提取概念並建立文章...")
    concept_events = extract_concepts_from_issues(issues)
    created_concepts = 0
    updated_files_by_concept = {}
    
    for name, related in concept_events.items():
        if related:  # 只建立有相關事件的概念
            try:
                c_file = compile_concept(name, related)
                created_concepts += 1
                
                # 收集這個主題的相關檔案 (概念本身 + 它所牽涉的今日新事件)
                associated_files = [c_file]
                for issue in related:
                    safe_title = re.sub(r'[<>:"/\\|?*]', '_', issue["title"])
                    e_file = EVENTS_DIR / f"{issue['date']}_{safe_title}.md"
                    if e_file.exists():
                        associated_files.append(e_file)
                updated_files_by_concept[name] = associated_files
                
                print(f"   📄 {name} ({len(related)} 則相關事件)")
            except Exception as e:
                print(f"   ⚠️ 跳過概念 {name}: {e}")
    print(f"   ✅ 完成 {created_concepts} 篇概念文章")
    
    # Step 4: 建立索引
    print("\n📋 建立全域索引...")
    build_index(issues, concept_events)
    print("   ✅ _index.md")
    
    print("\n📅 建立時間線...")
    build_timeline(issues)
    print("   ✅ _timeline.md")
    
    print("\n🏛️ 建立實體名錄...")
    build_entities(issues)
    print("   ✅ _entities.md")
    
    # Step 5: 執行團隊版控 (為每個有變更的主題發送 PR)
    if "--team-sync" in sys.argv:
        print("\n🤝 啟動 20人團隊協作同步：派發 Pull Requests...")
        # 確保全域檔案也被納入某些 PR，這裡簡單起見一併給第一個 PR 或忽略
        for concept_name, files in updated_files_by_concept.items():
            # 我們也附上 index 和 timeline
            files.extend([WIKI_DIR / "_index.md", WIKI_DIR / "_timeline.md", WIKI_DIR / "_entities.md"])
            # 去除重複
            files = list(set(files))
            push_pr_for_topic(concept_name, files)
    
    # 統計
    print("\n" + "=" * 60)
    print(f"  📊 知識庫初始化完成！")
    print(f"     概念文章：{created_concepts} 篇")
    print(f"     事件卡片：{created_events} 張")
    print(f"     索引檔案：3 份")
    print(f"     Wiki 路徑：{WIKI_DIR}")
    print("=" * 60)
    print("\n💡 請在 Obsidian 中開啟 wiki/ 資料夾作為 Vault")
    print("   然後點擊 _index.md 開始瀏覽你的情報知識圖譜！")


if __name__ == "__main__":
    main()
