"""
handover_check.py — 交接文件自動觸發器
=========================================
被 .claude/settings.json 的 Hook 系統呼叫：
  --precompact : 對話壓縮前注入指示（PreCompact hook）
  --stop       : 對話結束前強制寫交接（Stop hook）
"""

import json
import sys
import time
from pathlib import Path

# Windows 終端編碼修正
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

HANDOVER_FILE = Path(
    r"C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新\HANDOVER.md"
)
FRESHNESS_SEC = 600  # 10 分鐘內更新過 → 視為已交接

HANDOVER_TEMPLATE = """\
請使用 Write 工具，立刻將以下結構寫入 HANDOVER.md，\
每個章節請根據本輪實際對話內容填寫（禁止留空白或寫「待補」）：

---
# 🤖 AI 協作交接文件

> **給接手的 Claude Code：**
> 以下是本輪對話的完整工作進度。請基於此繼續協助 User。

## 1. 系統當前狀態 (System Status)
（描述目前各子系統的運作狀況：analysis.py / wiki_compiler.py / LINE Webhook / GitHub sync）

## 2. 本輪已完成的重大變更 (Recent Changes)
（條列本次對話中實際建立或修改的檔案與功能）

## 3. 目前面臨的問題 / 待解決事項 (Pending Fixes)
（列出已知 bug、未測試功能、HANDOVER.md 中 Antigravity 留下的待辦）

## 4. 下一階段發展建議 (Next Steps)
（下一輪 Claude 應該優先做的 3 件事）

---
"""


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--stop"
    now = time.time()

    # 計算 HANDOVER.md 距今多少秒
    if HANDOVER_FILE.exists():
        age_sec = now - HANDOVER_FILE.stat().st_mtime
    else:
        age_sec = float("inf")

    if mode == "--precompact":
        # ── PreCompact：對話即將壓縮，注入強制指令 ──────────────
        output = {
            "additionalContext": (
                "⚠️  CRITICAL — 對話即將自動壓縮（Context Window 不足）\n\n"
                "在壓縮前，你【必須立刻】完成以下步驟，否則所有進度將遺失：\n\n"
                + HANDOVER_TEMPLATE +
                "\n寫完後，再允許壓縮繼續。"
            )
        }

    elif mode == "--stop":
        if age_sec > FRESHNESS_SEC:
            # ── HANDOVER.md 不存在或超過 10 分鐘未更新 → 強制繼續 ──
            minutes = int(age_sec / 60) if age_sec != float("inf") else "∞"
            output = {
                "continue": False,
                "stopReason": (
                    f"⚠️  系統規則：HANDOVER.md 距上次更新已達 {minutes} 分鐘（或不存在）。\n"
                    "本輪對話必須先完成交接才能結束。\n\n"
                    + HANDOVER_TEMPLATE
                )
            }
        else:
            # ── 已在 10 分鐘內更新過 → 正常結束 ──────────────────
            output = {
                "systemMessage": (
                    f"✅ HANDOVER.md 已於 {int(age_sec/60)} 分鐘前更新，交接完成。"
                )
            }

    else:
        output = {}

    # 輸出 JSON（UTF-8，不轉義中文）
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
