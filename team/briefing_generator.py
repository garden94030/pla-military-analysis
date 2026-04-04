"""
briefing_generator.py — 每日 Team Briefing 簡報生成器
=======================================================
功能：
  1. 掃描今日 _daily_output/ 的所有議題報告
  2. 合併全文 → 一封 Gmail（保持昨天格式）
  3. LINE 發送精簡摘要
  4. TESTING_MODE=true 時只寄到主信箱，不寄 BCC

用法：
  python team/briefing_generator.py             # 生成並推送
  python team/briefing_generator.py --no-push   # 只生成，不推送
"""

import json
import re
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE  = Path(r"C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新")
OUTPUT_DIR = WORKSPACE / "_daily_output"
TEAM_DIR   = WORKSPACE / "team"
ANALYSTS_F = TEAM_DIR / "analysts.json"
ENV_FILE   = WORKSPACE / ".env"

# ── 環境設定 ──
def _load_env() -> dict:
    cfg = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    return cfg

def _is_testing() -> bool:
    return _load_env().get("TESTING_MODE", "false").lower() == "true"

def _get_recipients() -> list[str]:
    cfg = _load_env()
    if _is_testing():
        primary = cfg.get("NOTIFICATION_EMAILS", "garden94030@gmail.com").split(",")[0].strip()
        print(f"  🧪 測試模式：只寄送至 {primary}")
        return [primary]
    all_r = cfg.get("NOTIFICATION_EMAILS", "garden94030@gmail.com")
    return [e.strip() for e in all_r.split(",") if e.strip()]

# ── 分析師對照表 ──
def _load_analysts() -> dict:
    raw = json.loads(ANALYSTS_F.read_text(encoding="utf-8"))
    return {a["github"]: a for a in raw.get("analysts", [])}

# ── 掃描今日議題 ──
def scan_today_issues(date_str: str) -> list[dict]:
    analysts_map = _load_analysts()
    issues = []
    dirs = sorted(OUTPUT_DIR.glob(f"{date_str}_議題*"))

    for d in dirs:
        if not d.is_dir():
            continue
        report_files = sorted(d.glob("*.md"))
        if not report_files:
            continue
        rep = report_files[-1]
        try:
            content = rep.read_text(encoding="utf-8")
        except Exception:
            content = ""

        issue_id, reviewer_github = "?", ""
        fm_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if fm_match:
            fm = fm_match.group(1)
            id_m = re.search(r"issue_id:\s*(\d+)", fm)
            if id_m:
                issue_id = id_m.group(1)
            rev_m = re.search(r"reviewer:\s*@(\S+)", fm)
            if rev_m:
                reviewer_github = rev_m.group(1)

        # fallback: parse from folder name
        if issue_id == "?":
            nm = re.search(r"_議題(\d+)_", d.name)
            if nm:
                issue_id = nm.group(1)

        title_m = re.search(r"^# (.+)", content, re.M)
        title = title_m.group(1).strip() if title_m else d.name

        esm = re.search(r"## 一[、.]?\s*執行摘要.*?\n+(.*?)(?=\n##|\Z)", content, re.DOTALL)
        exec_summary = esm.group(1).strip()[:200].replace("\n", " ") if esm else ""

        analyst_info = analysts_map.get(reviewer_github, {})
        expert_name = analyst_info.get("name", reviewer_github or "未分配")

        risk = "🟡 中"
        if any(kw in title + content[:500] for kw in ["緊急", "警示", "武力", "飛彈齊射", "封鎖", "登陸"]):
            risk = "🔴 高"
        elif any(kw in title + content[:500] for kw in ["例行", "常規", "日常巡邏"]):
            risk = "🟢 低"

        issues.append({
            "issue_id": issue_id,
            "title": title,
            "expert_name": expert_name,
            "expert_github": reviewer_github,
            "exec_summary": exec_summary,
            "risk": risk,
            "kml": bool(list(d.glob("*.kml"))),
            "folder": d.name,
            "report_path": rep,
            "full_content": content,
        })

    return issues

# ── 合併全文（Gmail 完整格式）──
def generate_merged_full_report(date_str: str, issues: list[dict]) -> str:
    """
    將所有今日報告合併為一份完整 Markdown，
    保留 front matter、HTML 跟超連結，與昨天格式一致。
    """
    today_fmt = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    now_fmt   = datetime.now().strftime("%H:%M")
    total     = len(issues)

    # 建立每份報告的 reviewer 显示字串
    def reviewer_str(iss: dict) -> str:
        gh = iss["expert_github"]
        name = iss["expert_name"]
        return f"@{gh} ({name})" if gh else name

    parts = []

    for i, iss in enumerate(issues, 1):
        # --- front matter 區塊 ---
        fm_block = (
            f"title: {iss['title']}\n"
            f"date: {today_fmt}\n"
            f"type: assessment\n"
            f"status: draft\n"
            f"author: Antigravity-Compiler\n"
            f"reviewer: {reviewer_str(iss)}\n"
        )

        # --- 去除原始 front matter，保留正文 ---
        body = iss["full_content"]
        body = re.sub(r"^---\n.*?\n---\n\n?", "", body, flags=re.DOTALL)

        # --- 如果多場，加分隔線 ---
        if total > 1:
            sep = f"---\n\n## 📄 報告 {i}/{total}\n\n"
        else:
            sep = ""

        parts.append(
            f"{sep}"
            f"{fm_block}\n"
            f"{body}\n"
        )

    return "\n\n".join(parts)

# ── LINE 摘要格式 ──
def generate_line_summary(date_str: str, issues: list[dict]) -> str:
    today_fmt = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    high  = [i for i in issues if "🔴" in i["risk"]]
    total = len(issues)

    lines = [
        f"🛡️ {today_fmt} 中共軍事動態簡報",
        f"━━━━━━━━━━━━━━━━━━━━━",
        f"📊 今日分析：共 {total} 議題",
        f"🔴 高風險：{len(high)} 件 | 🟡 中：{sum(1 for i in issues if '🟡' in i['risk'])} 件",
        "",
    ]
    if high:
        lines.append("⚠️ 高風險議題：")
        for iss in high[:3]:
            lines.append(f"  • [{iss['issue_id']}] {iss['title'][:30]}")
            lines.append(f"    👤 {iss['expert_name']}")
        lines.append("")

    lines.append("📋 今日所有議題：")
    for iss in issues[:8]:
        lines.append(f"  {iss['risk']} [{iss['issue_id']}] {iss['title'][:25]}")
    if total > 8:
        lines.append(f"  ...另有 {total - 8} 則，詳見完整報告")

    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        "📧 完整報告已寄至 Gmail",
        "📂 Obsidian: wiki/events/ 同步完成",
    ])
    return "\n".join(lines)

# ── 生成簡報 MD ──
def generate_briefing_md(date_str: str, issues: list[dict]) -> str:
    today_fmt = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    now_fmt   = datetime.now().strftime("%H:%M")
    total     = len(issues)
    high = [i for i in issues if "🔴" in i["risk"]]
    mid  = [i for i in issues if "🟡" in i["risk"]]
    low  = [i for i in issues if "🟢" in i["risk"]]

    lines = [
        f"# 🛡️ {today_fmt} 中共軍事動態 · 每日團隊簡報",
        f"> 由「20人中共軍事動態研析專家團隊」自動生成 | {now_fmt} 產出 | 共 {total} 個議題",
        "", "---", "",
        "## 📊 風險概覽", "",
        "| 等級 | 數量 |", "|------|------|",
        f"| 🔴 高風險 | {len(high)} 件 |",
        f"| 🟡 中風險 | {len(mid)} 件 |",
        f"| 🟢 低風險 | {len(low)} 件 |",
        f"| **合計** | **{total} 件** |", "",
    ]

    if high:
        lines += ["## 🔴 高風險議題（需立即關注）", ""]
        for iss in high:
            lines += [
                f"### 議題 {iss['issue_id']}：{iss['title']}",
                f"- **負責分析師**：{iss['expert_name']} (`@{iss['expert_github']}`)",
                f"- **執行摘要**：{iss['exec_summary'] or '（無摘要）'}...",
                ("- **地理資訊**：✅ KML 已生成" if iss["kml"] else ""), "",
            ]

    lines += ["## 📋 今日議題完整清單", "", "| # | 議題標題 | 負責分析師 | 風險 | GIS |",
              "|---|----------|-----------|------|-----|"]
    for iss in issues:
        kml_icon = "🗺️" if iss["kml"] else "—"
        lines.append(f"| {iss['issue_id']} | {iss['title'][:40]} | {iss['expert_name']} | {iss['risk']} | {kml_icon} |")

    lines += ["", "## 👥 今日分析師出席", ""]
    expert_count: dict[str, int] = {}
    for iss in issues:
        expert_count[iss["expert_name"]] = expert_count.get(iss["expert_name"], 0) + 1
    for name, cnt in sorted(expert_count.items(), key=lambda x: -x[1]):
        lines.append(f"- **{name}**：負責 {cnt} 個議題")

    lines += ["", "---",
              f"*本簡報由自動化系統生成，完整報告請見 `_daily_output/{date_str}_*/` 資料夾*"]
    return "\n".join(lines)

# ── 主函式 ──
def generate_and_send(date_str: str = None, push: bool = True) -> Path:
    if not date_str:
        date_str = datetime.now().strftime("%Y%m%d")

    print(f"\n📊 生成 {date_str} 每日簡報...")
    issues = scan_today_issues(date_str)

    if not issues:
        print(f"  ⚠️  {date_str} 無任何議題，跳過簡報生成。")
        return None

    print(f"  → 共找到 {len(issues)} 個議題，合併為一份完整通知")

    # 生成簡報 MD
    briefing_md   = generate_briefing_md(date_str, issues)
    briefing_path = OUTPUT_DIR / f"{date_str}_團隊每日簡報.md"
    briefing_path.write_text(briefing_md, encoding="utf-8")
    print(f"  ✅ 簡報 MD 已生成: {briefing_path.name}")

    # 同步 Obsidian
    wiki_events = WORKSPACE / "wiki" / "events"
    os.makedirs(wiki_events, exist_ok=True)
    shutil.copy2(briefing_path, wiki_events / f"{date_str}_團隊每日簡報.md")
    print(f"  📒 已同步至 Obsidian wiki/events/")

    if push:
        _push_notifications(date_str, issues)

    return briefing_path

def _push_notifications(date_str: str, issues: list[dict]):
    """合併全文 → Gmail；精簡摘要 → LINE"""
    try:
        sys.path.insert(0, str(WORKSPACE))
        from notifier import EmailNotifier, LineBotNotifier
    except ImportError:
        print("  ⚠️  notifier.py 無法載入，跳過推送")
        return

    recipients = _get_recipients()
    today_fmt  = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    high_cnt   = sum(1 for i in issues if "🔴" in i["risk"])
    subject    = (f"🔍 中共軍事動態分析報告 — {today_fmt} | "
                  f"{len(issues)} 議題 · 🔴 {high_cnt} 高風險")

    print(f"\n📤 推送通知...")

    # Gmail — 將合併內容寫入臨時檔再發送（保留 HTML 與超連結）
    try:
        import tempfile
        merged_md = generate_merged_full_report(date_str, issues)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".md", delete=False
        ) as tmp:
            tmp.write(merged_md)
            tmp_path = Path(tmp.name)
        email = EmailNotifier(recipients=recipients)
        ok = email.send_report(tmp_path, subject=subject)
        tmp_path.unlink(missing_ok=True)
        print(f"  {'✅' if ok else '❌'} Gmail：{'已發送至 ' + ', '.join(recipients) if ok else '發送失敗'}")
    except Exception as e:
        print(f"  ❌ Gmail 錯誤：{e}")

    # LINE — 精簡摘要
    try:
        line_text = generate_line_summary(date_str, issues)
        line = LineBotNotifier()
        ok = line.send_text(line_text)
        print(f"  {'✅' if ok else '❌'} LINE：{'已發送' if ok else '發送失敗（請確認 LINE Bot 設定）'}")
    except Exception as e:
        print(f"  ❌ LINE 錯誤：{e}")

if __name__ == "__main__":
    push     = "--no-push" not in sys.argv
    date_arg = None
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--date" and i < len(sys.argv):
            date_arg = sys.argv[i + 1]
        elif arg.startswith("--date="):
            date_arg = arg.split("=", 1)[1]
    result = generate_and_send(date_str=date_arg, push=push)
    if result:
        print(f"\n🎉 完成！簡報路徑：{result}")
