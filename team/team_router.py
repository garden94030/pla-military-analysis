"""
team_router.py — 虛擬團隊議題自動路由
======================================
根據文章標題/關鍵字，自動比對最適合的虛擬分析師角色。

用法：
  from team.team_router import route_topic
  analyst = route_topic("055型驅逐艦南海演習")
  # → {"id": "analyst-navy-01", "name": "海軍分析師-01", ...}

  python team/team_router.py "釣魚台海警巡邏"
"""

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ANALYSTS_FILE = Path(__file__).parent / "analysts.json"


def load_analysts() -> list:
    data = json.loads(ANALYSTS_FILE.read_text(encoding="utf-8"))
    return data.get("analysts", [])


def route_topic(title: str, fallback_id: str = "garde") -> dict:
    """
    比對標題關鍵字，回傳最適分析師 dict。
    若無匹配，回傳 fallback（預設首席分析師 garde）。
    """
    analysts = load_analysts()
    title_lower = title.lower()

    best_match = None
    best_score = 0

    for analyst in analysts:
        score = 0
        for keyword in analyst.get("auto_assign_topics", []):
            if keyword.lower() in title_lower:
                score += 1
        if score > best_score:
            best_score = score
            best_match = analyst

    if best_match:
        return best_match

    # fallback
    for analyst in analysts:
        if analyst["id"] == fallback_id:
            return analyst
    return analysts[0]


def route_batch(titles: list[str]) -> list[dict]:
    """批次路由多個議題標題，回傳 [{title, analyst}, ...]"""
    return [{"title": t, "analyst": route_topic(t)} for t in titles]


def print_team_roster():
    """列印完整虛擬團隊名單"""
    analysts = load_analysts()
    print(f"\n{'='*55}")
    print(f"  🛡️  PLA 情報分析虛擬團隊  ({len(analysts)} 人)")
    print(f"{'='*55}")
    roles_seen = {}
    for a in analysts:
        role = a["role"]
        if role not in roles_seen:
            roles_seen[role] = []
        roles_seen[role].append(a)

    role_labels = {
        "director": "🎯 首席/戰略",
        "naval-expert": "⚓ 海軍專家",
        "air-expert": "✈️  空軍專家",
        "rocket-expert": "🚀 火箭軍專家",
        "cyber-expert": "💻 網路/電磁",
        "space-expert": "🛰️  太空專家",
        "taiwan-expert": "🗺️  台海專家",
        "regional-expert": "🌏 區域專家",
        "osint-expert": "🔍 OSINT專家",
        "linguist": "📖 語言/政工",
        "tech-expert": "⚙️  軍工技術",
        "assessor": "📊 戰略評估",
        "reviewer": "✅ 品質管制",
    }

    for role, members in roles_seen.items():
        label = role_labels.get(role, role)
        for m in members:
            focus_str = "、".join(m["focus"][:2])
            print(f"  {label:<14}  {m['name']:<14}  [{focus_str}]")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        title = " ".join(sys.argv[1:])
        result = route_topic(title)
        print(f"\n議題：「{title}」")
        print(f"→ 指派給：{result['name']} ({result['role']})")
        print(f"   專長：{'、'.join(result['focus'])}")
        print(f"   GitHub：@{result['github']}\n")
    else:
        print_team_roster()
