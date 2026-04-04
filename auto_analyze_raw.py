"""
auto_analyze_raw.py — wiki/raw/ 新檔案自動分析觸發器
=======================================================
由 .claude/settings.json PostToolUse Hook 自動呼叫（每次 Write/Edit 後觸發）。

功能：
  1. 掃描 wiki/raw/*.md，找出尚未分析的新檔案
  2. 比對 _processed_raw_log.json（已處理清單），跳過舊檔
  3. 提取 frontmatter title/source + 正文前 600 字
  4. 呼叫 team_router.py 自動路由到最適分析師
  5. 將 raw 內容複製為 _daily_input/{date}_{slug}.txt，供 analysis.py 使用
  6. 更新 _processed_raw_log.json，避免重複處理

用法：
  python auto_analyze_raw.py              # 標準執行（PostToolUse Hook 自動呼叫）
  python auto_analyze_raw.py --dry-run    # 列出待處理清單，不執行
  python auto_analyze_raw.py --reset      # 清空 log，強制重新處理所有檔案
  python auto_analyze_raw.py --force FILE # 強制重新處理指定檔案
"""

import json
import re
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── 路徑常數 ──────────────────────────────────────────────────────────────────
WORKSPACE    = Path(r"C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新")
RAW_DIR      = WORKSPACE / "wiki" / "raw"
INPUT_DIR    = WORKSPACE / "_daily_input"
LOG_FILE     = WORKSPACE / "_processed_raw_log.json"
TEAM_DIR     = WORKSPACE / "team"

# ── 已處理 Log 管理 ───────────────────────────────────────────────────────────
def load_log() -> Dict[str, Any]:
    """載入已處理清單（{filename: {processed_at, analyst_id, topic}}）"""
    if LOG_FILE.exists():
        try:
            return json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_log(log: Dict[str, Any]) -> None:
    LOG_FILE.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")

def is_processed(filename: str, log: Dict[str, Any]) -> bool:
    return filename in log

# ── Frontmatter 解析 ──────────────────────────────────────────────────────────
def parse_frontmatter(content: str) -> Dict[str, str]:
    """解析 YAML frontmatter，回傳 {title, source, author, description}"""
    result = {"title": "", "source": "", "author": "", "description": ""}
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return result
    fm_text = fm_match.group(1)
    for key in result:
        m = re.search(rf'^{key}:\s*["\']?(.*?)["\']?\s*$', fm_text, re.MULTILINE)
        if m:
            result[key] = m.group(1).strip().strip('"').strip("'")
    return result

def extract_body(content: str, max_chars: int = 600) -> str:
    """去除 frontmatter，取正文前 max_chars 字"""
    body = re.sub(r"^---\n.*?\n---\n\n?", "", content, flags=re.DOTALL)
    # 去除 Markdown 圖片語法 ![...](...)
    body = re.sub(r"!\[.*?\]\(.*?\)", "", body)
    # 去除空行
    body = "\n".join(line for line in body.splitlines() if line.strip())
    return body[:max_chars].strip()

# ── 自動路由 ──────────────────────────────────────────────────────────────────
def route_raw_file(title: str, body: str) -> Dict[str, Any]:
    """呼叫 team_router，依標題+正文關鍵字選出最適分析師"""
    try:
        sys.path.insert(0, str(WORKSPACE))
        from team.team_router import route_topic
        # 合併標題+摘要作為路由輸入
        combined = f"{title} {body[:200]}"
        return route_topic(combined)
    except Exception as e:
        # fallback：回傳首席分析師
        return {
            "id": "garde",
            "name": "首席分析師 (Chief-Analyst)",
            "role": "director",
            "focus": ["戰略合成"],
            "github": "garden94030",
        }

# ── 建立 _daily_input 任務檔 ──────────────────────────────────────────────────
def create_input_task(
    raw_file: Path,
    title: str,
    source: str,
    body: str,
    analyst: Dict[str, Any],
    date_str: str,
) -> Path:
    """
    將 raw 檔內容包裝為 _daily_input/{date}_{slug}.txt，
    格式與 gmail_reader.py 產出一致，供 analysis.py 讀取。
    """
    INPUT_DIR.mkdir(exist_ok=True)

    # 清理檔名（移除特殊字元）
    slug = re.sub(r"[^\w\u4e00-\u9fff\-]", "_", raw_file.stem)[:40]
    out_path = INPUT_DIR / f"{date_str}_raw_{slug}.txt"

    now_tw = datetime.now().strftime("%Y-%m-%d %H:%M")
    content = f"""來源類型: Obsidian Web Clipper (wiki/raw/)
原始檔案: {raw_file.name}
文章標題: {title}
原始來源: {source}
建立時間: {now_tw}（台北時間 UTC+8）
指派分析師: {analyst['name']} ({analyst['id']})
分析師專長: {'、'.join(analyst.get('focus', [])[:3])}

--- 原文摘要 ---
{body}

--- 完整原文路徑 ---
{raw_file}
"""
    out_path.write_text(content, encoding="utf-8")
    return out_path


# ── 核心掃描邏輯 ──────────────────────────────────────────────────────────────
def scan_and_queue(
    dry_run: bool = False,
    force_file: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    掃描 wiki/raw/ → 找出未處理檔案 → 建立 _daily_input 任務。

    Returns:
        list of {filename, title, source, analyst, input_path, status}
    """
    if not RAW_DIR.exists():
        print(f"  ⚠️  wiki/raw/ 不存在：{RAW_DIR}")
        return []

    raw_files = sorted(RAW_DIR.glob("*.md"))
    if not raw_files:
        print("  ℹ️  wiki/raw/ 中無 .md 檔案")
        return []

    log = load_log()
    date_str = datetime.now().strftime("%Y%m%d")
    results = []
    new_count = 0

    for raw_file in raw_files:
        filename = raw_file.name

        # 強制模式
        if force_file and force_file not in filename:
            continue

        # 跳過已處理（非強制模式）
        if not force_file and is_processed(filename, log):
            continue

        # 讀取內容
        try:
            content = raw_file.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"  ❌ 無法讀取 {filename}: {e}")
            continue

        fm   = parse_frontmatter(content)
        body = extract_body(content, max_chars=600)

        title  = fm["title"] or raw_file.stem
        source = fm["source"] or "未知來源"

        # 路由
        analyst = route_raw_file(title, body)

        print(f"  📄 {filename[:50]}")
        print(f"     標題：{title[:60]}")
        print(f"     來源：{source[:60]}")
        print(f"     → 指派：{analyst['name']} ({analyst['id']})")

        entry = {
            "filename": filename,
            "title": title,
            "source": source,
            "analyst_id": analyst["id"],
            "analyst_name": analyst["name"],
            "input_path": None,
            "status": "dry-run" if dry_run else "queued",
        }

        if not dry_run:
            try:
                input_path = create_input_task(raw_file, title, source, body, analyst, date_str)
                entry["input_path"] = str(input_path)
                entry["status"] = "queued"
                print(f"     ✅ 已建立任務：{input_path.name}")
                new_count += 1

                # 更新 log
                log[filename] = {
                    "processed_at": datetime.now().isoformat(),
                    "analyst_id": analyst["id"],
                    "title": title,
                    "source": source,
                    "input_task": input_path.name,
                }
                save_log(log)

            except Exception as e:
                entry["status"] = f"error: {e}"
                print(f"     ❌ 建立任務失敗：{e}")
        else:
            print(f"     [DRY RUN] 不建立任務")

        results.append(entry)
        print()

    if not dry_run and new_count > 0:
        print(f"  📥 共建立 {new_count} 個新任務至 _daily_input/")
        print(f"  💡 執行 `python analysis.py` 開始分析這些任務")
    elif not dry_run and new_count == 0 and not force_file:
        print(f"  ✅ wiki/raw/ 所有檔案已處理完畢（共 {len(log)} 筆記錄）")

    return results


def reset_log() -> None:
    """清空已處理 log，強制重新處理所有 raw 檔"""
    if LOG_FILE.exists():
        backup = LOG_FILE.with_suffix(".json.bak")
        shutil.copy2(LOG_FILE, backup)
        print(f"  📦 已備份舊 log 至 {backup.name}")
    LOG_FILE.write_text("{}", encoding="utf-8")
    print(f"  🔄 已清空 _processed_raw_log.json，下次執行將重新處理所有 raw 檔")


def show_status() -> None:
    """顯示 wiki/raw/ 與處理狀態摘要"""
    raw_files = sorted(RAW_DIR.glob("*.md")) if RAW_DIR.exists() else []
    log = load_log()
    processed = set(log.keys())
    unprocessed = [f for f in raw_files if f.name not in processed]

    print(f"\n{'='*60}")
    print(f"  🔍 wiki/raw/ 狀態報告")
    print(f"{'='*60}")
    print(f"  總檔案數：{len(raw_files)}")
    print(f"  已處理：  {len(processed)}")
    print(f"  待處理：  {len(unprocessed)}")

    if unprocessed:
        print(f"\n  📋 待處理清單：")
        for f in unprocessed:
            print(f"    ⏳ {f.name[:60]}")

    if processed:
        print(f"\n  ✅ 已處理清單（最近5筆）：")
        recent = sorted(log.items(), key=lambda x: x[1].get("processed_at",""), reverse=True)[:5]
        for fname, info in recent:
            ts = info.get("processed_at","")[:16]
            analyst = info.get("analyst_id","?")
            print(f"    [{ts}] {fname[:40]} → @{analyst}")

    print(f"{'='*60}\n")


# ── CLI 入口 ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="wiki/raw/ 新檔案自動分析觸發器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python auto_analyze_raw.py              # 標準執行（Hook自動呼叫）
  python auto_analyze_raw.py --dry-run    # 列出待處理，不建立任務
  python auto_analyze_raw.py --status     # 顯示整體狀態
  python auto_analyze_raw.py --reset      # 清空log，重新處理所有
  python auto_analyze_raw.py --force "Thread by @BRPSierraMadre"  # 強制重新處理
        """
    )
    parser.add_argument("--dry-run", action="store_true", help="列出待處理清單，不執行")
    parser.add_argument("--reset",   action="store_true", help="清空已處理log")
    parser.add_argument("--status",  action="store_true", help="顯示狀態報告")
    parser.add_argument("--force",   type=str,            help="強制重新處理含此關鍵字的檔案")

    args = parser.parse_args()

    if args.reset:
        reset_log()
        sys.exit(0)

    if args.status:
        show_status()
        sys.exit(0)

    # 標準執行 / dry-run / force
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    mode = "DRY RUN" if args.dry_run else ("FORCE: " + args.force if args.force else "SCAN")
    print(f"\n🔍 auto_analyze_raw.py [{mode}] — {now}（台北時間 UTC+8）")
    print(f"   掃描路徑：{RAW_DIR}")
    print()

    results = scan_and_queue(
        dry_run=args.dry_run,
        force_file=args.force,
    )

    if not args.dry_run and results:
        total   = len(results)
        success = sum(1 for r in results if r["status"] == "queued")
        print(f"\n📊 完成：{success}/{total} 個任務已加入佇列")
