"""
wiki_health.py — 情報知識庫健康度監控
========================================
功能：
  1. 掃描 GitHub 開放 Pull Requests（待審核）
  2. 找出超過 7 天未更新的 draft 概念文章
  3. 顯示 _daily_input/ 待處理佇列
  4. 找出沒有 reviewer 的 draft 文章
  5. 輸出健康報告到終端 + _system/health_report.md

用法：
  python wiki_health.py          # 顯示健康報告
  python wiki_health.py --fix    # 自動指派 reviewer（輪派）
"""

import os
import sys
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding="utf-8")

# ── 路徑設定 ─────────────────────────────────────────────
WORKSPACE   = Path(r"C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新")
WIKI_DIR    = WORKSPACE / "wiki"
CONCEPTS    = WIKI_DIR / "concepts"
EVENTS      = WIKI_DIR / "events"
INPUT_DIR   = WORKSPACE / "_daily_input"
SYSTEM_DIR  = WORKSPACE / "_system"
SYSTEM_DIR.mkdir(exist_ok=True)

# ── 20人虛擬團隊 reviewer 輪派清單（從 team/analysts.json 載入）────
def _load_team_reviewers() -> list:
    analysts_file = WORKSPACE / "team" / "analysts.json"
    if analysts_file.exists():
        data = json.loads(analysts_file.read_text(encoding="utf-8"))
        return [a["github"] for a in data.get("analysts", [])]
    return ["garde"]  # fallback

TEAM_REVIEWERS = _load_team_reviewers()

STALE_DAYS = 7  # 超過幾天未更新視為 stale


# ── 工具函數 ─────────────────────────────────────────────
def parse_frontmatter(text: str) -> dict:
    """解析 YAML frontmatter"""
    meta = {}
    if not text.startswith("---"):
        return meta
    end = text.find("---", 3)
    if end == -1:
        return meta
    block = text[3:end]
    for line in block.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


def file_age_days(path: Path) -> float:
    """計算檔案距今天數"""
    mtime = path.stat().st_mtime
    return (datetime.now().timestamp() - mtime) / 86400


# ── 1. GitHub 開放 PR ──────────────────────────────────
def check_open_prs() -> list:
    """列出所有開放中的 Pull Requests"""
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--state", "open",
             "--json", "number,title,createdAt,author,headRefName"],
            cwd=WORKSPACE, capture_output=True, text=True, encoding="utf-8"
        )
        if result.returncode != 0:
            return []
        prs = json.loads(result.stdout)
        return prs
    except Exception:
        return []


# ── 2. Stale draft 概念文章 ────────────────────────────
def check_stale_concepts() -> list:
    """找出超過 STALE_DAYS 天未更新的 draft 概念"""
    stale = []
    if not CONCEPTS.exists():
        return stale
    for f in CONCEPTS.glob("*.md"):
        age = file_age_days(f)
        if age >= STALE_DAYS:
            meta = parse_frontmatter(f.read_text(encoding="utf-8", errors="ignore"))
            if meta.get("status", "draft") == "draft":
                stale.append({
                    "file": f.name,
                    "age_days": round(age, 1),
                    "reviewer": meta.get("reviewer", "待指派"),
                })
    return sorted(stale, key=lambda x: x["age_days"], reverse=True)


# ── 3. 待處理佇列 ─────────────────────────────────────
def check_input_queue() -> list:
    """列出 _daily_input/ 中等待分析的檔案"""
    if not INPUT_DIR.exists():
        return []
    files = [f for f in INPUT_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]
    return sorted(files, key=lambda f: f.stat().st_mtime)


# ── 4. 無 reviewer 的 draft ──────────────────────────
def check_unassigned_drafts() -> list:
    """找出 reviewer 為「待指派」的 draft 文章"""
    unassigned = []
    for folder in [CONCEPTS, EVENTS]:
        if not folder.exists():
            continue
        for f in folder.glob("*.md"):
            meta = parse_frontmatter(f.read_text(encoding="utf-8", errors="ignore"))
            if meta.get("status") == "draft" and meta.get("reviewer") in ("待指派", "", None):
                unassigned.append({
                    "file": f.name,
                    "folder": folder.name,
                    "title": meta.get("title", f.stem),
                })
    return unassigned[:20]  # 最多顯示 20 筆


# ── 5. Auto-assign reviewer（--fix 模式） ─────────────
def auto_assign_reviewers(unassigned: list):
    """輪派 reviewer 給未指派的 draft 文章"""
    if not unassigned:
        return
    reviewer_idx = 0
    fixed = 0
    for item in unassigned:
        folder = CONCEPTS if item["folder"] == "concepts" else EVENTS
        f = folder / item["file"]
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        reviewer = TEAM_REVIEWERS[reviewer_idx % len(TEAM_REVIEWERS)]
        text = text.replace("reviewer: 待指派", f"reviewer: {reviewer}", 1)
        f.write_text(text, encoding="utf-8")
        reviewer_idx += 1
        fixed += 1
    print(f"✅ 已自動指派 {fixed} 篇文章的 reviewer")


# ── 報告生成 ──────────────────────────────────────────
def generate_report(prs, stale, queue, unassigned) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 健康度評分
    score = 100
    if len(prs) > 5:   score -= 20
    elif len(prs) > 0: score -= len(prs) * 3
    if len(stale) > 3:  score -= 15
    if len(queue) > 5:  score -= 10
    if len(unassigned) > 10: score -= 10

    if score >= 85:   status_emoji = "🟢"
    elif score >= 60: status_emoji = "🟡"
    else:             status_emoji = "🔴"

    lines = [
        f"# 📊 知識庫健康度報告",
        f"",
        f"**更新時間**：{now}",
        f"**健康評分**：{status_emoji} {score}/100",
        f"",
        f"---",
        f"",
    ]

    # PR 狀態
    lines += [f"## 🔀 GitHub Pull Requests（{len(prs)} 個待審）", ""]
    if prs:
        for pr in prs[:10]:
            created = pr.get("createdAt", "")[:10]
            author  = pr.get("author", {}).get("login", "?")
            title   = pr.get("title", "")
            num     = pr.get("number", "?")
            lines.append(f"- **#{num}** `{created}` @{author} — {title}")
        if len(prs) > 10:
            lines.append(f"- ⚠️ ... 尚有 {len(prs)-10} 個 PR 未列出")
    else:
        lines.append("✅ 無待審 PR")
    lines.append("")

    # Stale 文章
    lines += [f"## 🕐 Stale 草稿（超過 {STALE_DAYS} 天未更新，共 {len(stale)} 篇）", ""]
    if stale:
        for item in stale[:10]:
            lines.append(f"- `{item['file']}` — {item['age_days']} 天，reviewer：{item['reviewer']}")
        if len(stale) > 10:
            lines.append(f"- ⚠️ ... 尚有 {len(stale)-10} 篇未列出")
    else:
        lines.append("✅ 無過期草稿")
    lines.append("")

    # 待處理佇列
    lines += [f"## 📥 _daily_input/ 待處理（{len(queue)} 個檔案）", ""]
    if queue:
        for f in queue[:8]:
            lines.append(f"- `{f.name}`")
        if len(queue) > 8:
            lines.append(f"- ... 尚有 {len(queue)-8} 個檔案")
        lines.append("")
        lines.append("> 💡 請執行 `python analysis.py` 或 `/daily-analysis` 處理")
    else:
        lines.append("✅ 佇列清空")
    lines.append("")

    # 無 reviewer
    lines += [f"## 👤 未指派 Reviewer（{len(unassigned)} 篇）", ""]
    if unassigned:
        for item in unassigned[:10]:
            lines.append(f"- `[{item['folder']}]` {item['title']}")
        if len(unassigned) > 10:
            lines.append(f"- ... 尚有 {len(unassigned)-10} 篇")
        lines.append("")
        lines.append("> 💡 執行 `python wiki_health.py --fix` 可自動輪派 reviewer")
    else:
        lines.append("✅ 所有文章已指派 reviewer")
    lines.append("")

    lines += [
        "---",
        f"",
        f"*本報告由 wiki_health.py 自動生成 | {now}*",
    ]

    return "\n".join(lines)


# ── 主程序 ────────────────────────────────────────────
def main():
    fix_mode = "--fix" in sys.argv

    print("=" * 60)
    print("  📊 中共軍事動態情報知識庫 — 健康度監控")
    print("=" * 60)

    print("\n🔍 [1/4] 掃描 GitHub Pull Requests...")
    prs = check_open_prs()
    print(f"   → 開放中 PR：{len(prs)} 個")

    print("\n🕐 [2/4] 掃描 stale 草稿...")
    stale = check_stale_concepts()
    print(f"   → 超過 {STALE_DAYS} 天未更新：{len(stale)} 篇")

    print("\n📥 [3/4] 掃描 _daily_input/ 佇列...")
    queue = check_input_queue()
    print(f"   → 待處理檔案：{len(queue)} 個")

    print("\n👤 [4/4] 掃描未指派 reviewer...")
    unassigned = check_unassigned_drafts()
    print(f"   → 未指派：{len(unassigned)} 篇")

    # 生成報告
    report = generate_report(prs, stale, queue, unassigned)

    # 輸出到 _system/
    report_file = SYSTEM_DIR / f"health_report_{datetime.now().strftime('%Y%m%d')}.md"
    report_file.write_text(report, encoding="utf-8")

    # 終端輸出摘要
    print("\n" + "=" * 60)
    score_line = [l for l in report.splitlines() if "健康評分" in l]
    if score_line:
        print("  " + score_line[0].replace("**", "").replace("：", ": "))
    print(f"\n  待審 PR：{len(prs)}  |  Stale 草稿：{len(stale)}  |  "
          f"待處理：{len(queue)}  |  無 reviewer：{len(unassigned)}")
    print("=" * 60)
    print(f"\n📄 完整報告已存入：{report_file.name}")

    if fix_mode:
        print("\n🔧 --fix 模式：自動指派 reviewer...")
        auto_assign_reviewers(unassigned)

    if len(queue) > 0:
        print(f"\n⚠️  _daily_input/ 有 {len(queue)} 個待處理檔案")
        print("   請執行：python analysis.py")
    if len(prs) > 5:
        print(f"\n⚠️  {len(prs)} 個 PR 積壓，請分析師盡快審查 GitHub")


if __name__ == "__main__":
    main()
