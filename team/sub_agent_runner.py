"""
sub_agent_runner.py — 20人分析師子代理人派遣系統
====================================================
使用 claude --dangerously-skip-permissions 啟動每位分析師的 Claude Code
子代理人，自動執行分析任務後回傳結果。

用法：
  # 派遣單一分析師
  python team/sub_agent_runner.py --analyst analyst-navy-01 --task "分析今日南海艦艇動態"

  # 批次派遣（依關鍵字自動路由）
  python team/sub_agent_runner.py --batch "055驅逐艦 南海演習 殲20 ADIZ"

  # 清單所有可用分析師
  python team/sub_agent_runner.py --list

  # 執行今日 _daily_input 的全員分析
  python team/sub_agent_runner.py --daily

架構說明：
  1. team_router.py 依關鍵字選出最匹配的分析師
  2. 讀取 team/profiles/{analyst_id}.CLAUDE.md 作為 system prompt
  3. 呼叫 `claude --dangerously-skip-permissions -p "{task}" --system-prompt-file "{profile}"`
  4. 捕獲輸出並寫入 _daily_output/
"""

import json
import sys
import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Any

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── 路徑常數 ──────────────────────────────────────────────────────────────────
WORKSPACE   = Path(r"C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新")
TEAM_DIR    = WORKSPACE / "team"
PROFILES_DIR = TEAM_DIR / "profiles"
ANALYSTS_F  = TEAM_DIR / "analysts.json"
OUTPUT_DIR  = WORKSPACE / "_daily_output"
INPUT_DIR   = WORKSPACE / "_daily_input"
WIKI_EVENTS = WORKSPACE / "wiki" / "events"

# claude.exe 或 claude 指令路徑（Windows 環境）
CLAUDE_CMD  = shutil.which("claude") or "claude"

# 最大並行分析師數量（避免 API rate limit）
MAX_PARALLEL = 3

# ── 載入分析師資料 ──────────────────────────────────────────────────────────────
def load_analysts() -> list[dict]:
    data = json.loads(ANALYSTS_F.read_text(encoding="utf-8"))
    return data.get("analysts", [])

def get_analyst(analyst_id: str) -> Optional[Dict]:
    for a in load_analysts():
        if a["id"] == analyst_id:
            return a
    return None

def get_profile_path(analyst_id: str) -> Path:
    return PROFILES_DIR / f"{analyst_id}.CLAUDE.md"

# ── 核心：啟動單一子代理人 ─────────────────────────────────────────────────────
def run_analyst(
    analyst_id: str,
    task: str,
    date_str: str = None,
    issue_num: str = "00",
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    呼叫 claude --dangerously-skip-permissions 啟動指定分析師子代理人。

    Returns:
        {
          "analyst_id": str,
          "analyst_name": str,
          "task": str,
          "success": bool,
          "output": str,      # stdout
          "error": str,       # stderr
          "duration_sec": float,
          "output_path": Path | None,
        }
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y%m%d")

    analyst = get_analyst(analyst_id)
    if not analyst:
        return {"analyst_id": analyst_id, "success": False, "error": f"找不到分析師 {analyst_id}"}

    profile_path = get_profile_path(analyst_id)
    if not profile_path.exists():
        return {"analyst_id": analyst_id, "success": False, "error": f"找不到子代理人配置檔：{profile_path}"}

    analyst_name = analyst["name"]
    role         = analyst["role"]

    # 輸出路徑：_daily_output/YYYYMMDD_議題XX_任務名稱/
    task_slug = task[:20].replace(" ", "_").replace("/", "_")
    out_dir   = OUTPUT_DIR / f"{date_str}_議題{issue_num}_{task_slug}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file  = out_dir / f"深度分析_{analyst_name}_{analyst_id}.md"

    # 建立傳入 claude 的完整 prompt
    now_tw = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_prompt = f"""
你是 {analyst_name}（{analyst_id}），角色：{role}。
現在是台北時間 {now_tw}（UTC+8）。

## 分析任務
{task}

## 輸出要求
1. 撰寫完整深度分析報告（至少 9 章，每章至少 300 字）
2. 使用 APA 第7版引用，每筆引用附 URL 或 DOI
3. 報告標頭加入 YAML frontmatter（title/type/status/author/reviewer/date/source）
4. 完成後將報告寫入：{out_file}
5. 同步寫入 Obsidian：{WIKI_EVENTS / f'{date_str}_{task_slug}.md'}

所有時間戳記使用台北時間（UTC+8）。
""".strip()

    print(f"\n🚀 派遣：{analyst_name} [{analyst_id}]")
    print(f"   任務：{task[:60]}...")
    print(f"   輸出：{out_dir.name}/")

    if dry_run:
        print(f"   [DRY RUN] 不實際執行")
        return {
            "analyst_id": analyst_id,
            "analyst_name": analyst_name,
            "task": task,
            "success": True,
            "output": "[DRY RUN]",
            "error": "",
            "duration_sec": 0.0,
            "output_path": out_file,
        }

    # ── 實際呼叫 claude CLI ──
    cmd = [
        CLAUDE_CMD,
        "--dangerously-skip-permissions",
        "--print",                        # 非互動模式，直接輸出
        "-p", full_prompt,
        "--system-prompt-file", str(profile_path),
    ]

    start = datetime.now()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=600,   # 10 分鐘上限
            cwd=str(WORKSPACE),
        )
        elapsed = (datetime.now() - start).total_seconds()
        success = (result.returncode == 0)
        output  = result.stdout or ""
        error   = result.stderr or ""

        if success and output.strip():
            # 如果 claude 輸出了 markdown 但沒有自己寫檔，幫它寫
            if not out_file.exists():
                out_file.write_text(output, encoding="utf-8")
                print(f"   ✅ 已寫入：{out_file.name}（{len(output)} chars）")
            else:
                print(f"   ✅ 分析師已自行寫入：{out_file.name}")
        elif not success:
            print(f"   ❌ 執行失敗（returncode={result.returncode}）")
            if error:
                print(f"   stderr: {error[:200]}")

        return {
            "analyst_id": analyst_id,
            "analyst_name": analyst_name,
            "task": task,
            "success": success,
            "output": output,
            "error": error,
            "duration_sec": elapsed,
            "output_path": out_file if out_file.exists() else None,
        }

    except subprocess.TimeoutExpired:
        return {
            "analyst_id": analyst_id,
            "analyst_name": analyst_name,
            "task": task,
            "success": False,
            "output": "",
            "error": "timeout (>600s)",
            "duration_sec": 600.0,
            "output_path": None,
        }
    except FileNotFoundError:
        return {
            "analyst_id": analyst_id,
            "analyst_name": analyst_name,
            "task": task,
            "success": False,
            "output": "",
            "error": f"找不到 claude 指令（{CLAUDE_CMD}）— 請確認 Claude Code CLI 已安裝並加入 PATH",
            "duration_sec": 0.0,
            "output_path": None,
        }
    except Exception as e:
        return {
            "analyst_id": analyst_id,
            "analyst_name": analyst_name,
            "task": task,
            "success": False,
            "output": "",
            "error": str(e),
            "duration_sec": 0.0,
            "output_path": None,
        }


# ── 批次派遣（自動路由） ────────────────────────────────────────────────────────
def run_batch(tasks: List[str], date_str: str = None, max_parallel: int = MAX_PARALLEL, dry_run: bool = False) -> List[Dict]:
    """
    批次派遣：每個 task 關鍵字自動路由到最適分析師，最多 max_parallel 個並行。
    """
    sys.path.insert(0, str(WORKSPACE))
    from team.team_router import route_topic

    if not date_str:
        date_str = datetime.now().strftime("%Y%m%d")

    jobs = []
    for idx, task in enumerate(tasks, 1):
        analyst = route_topic(task)
        issue_num = str(idx).zfill(2)
        jobs.append((analyst["id"], task, date_str, issue_num))

    print(f"\n📋 批次派遣：{len(jobs)} 個任務，最多 {max_parallel} 並行")
    print(f"{'─'*55}")
    for a_id, t, _, num in jobs:
        a = get_analyst(a_id)
        name = a["name"] if a else a_id
        print(f"  議題 {num}: {t[:40]:40s}  → {name}")
    print(f"{'─'*55}\n")

    results = []
    with ThreadPoolExecutor(max_workers=max_parallel) as pool:
        futures = {
            pool.submit(run_analyst, a_id, task, ds, num, dry_run): (a_id, task)
            for a_id, task, ds, num in jobs
        }
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            icon = "✅" if r["success"] else "❌"
            print(f"  {icon} [{r['analyst_id']}] {r['task'][:40]} ({r['duration_sec']:.1f}s)")

    return results


# ── 每日模式（掃描 _daily_input 並分配） ─────────────────────────────────────────
def run_daily(date_str: str = None, dry_run: bool = False):
    """掃描 _daily_input/*.txt 提取主題，批次派遣。"""
    if not date_str:
        date_str = datetime.now().strftime("%Y%m%d")

    txt_files = sorted(INPUT_DIR.glob("*.txt"))
    if not txt_files:
        print("  ⚠️  _daily_input/ 中無 .txt 檔案，請先執行 gmail_reader.py")
        return []

    tasks = []
    for f in txt_files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            # 取前 500 字作為任務摘要
            task_summary = f"分析以下情報（來源：{f.stem}）：\n\n{content[:500]}"
            tasks.append(task_summary)
        except Exception as e:
            print(f"  ⚠️  無法讀取 {f.name}: {e}")

    print(f"\n📥 每日模式：找到 {len(tasks)} 份輸入，開始批次派遣")
    return run_batch(tasks, date_str=date_str, dry_run=dry_run)


# ── 列出所有分析師 ─────────────────────────────────────────────────────────────
def list_analysts():
    analysts = load_analysts()
    print(f"\n{'='*65}")
    print(f"  🛡️  PLA 情報分析 — 20人子代理人團隊")
    print(f"{'='*65}")
    for a in analysts:
        profile = get_profile_path(a["id"])
        status = "✅" if profile.exists() else "❌ 無配置檔"
        focus = "、".join(a["focus"][:2])
        print(f"  {status}  {a['id']:<22s}  {a['name']:<18s}  [{focus}]")
    print(f"{'='*65}")
    print(f"  共 {len(analysts)} 位分析師 | 配置檔路徑：team/profiles/")
    print(f"  啟動方式：claude --dangerously-skip-permissions")
    print(f"{'='*65}\n")


# ── 生成執行摘要報告 ──────────────────────────────────────────────────────────
def print_summary(results: List[Dict]):
    if not results:
        return
    success = [r for r in results if r["success"]]
    failed  = [r for r in results if not r["success"]]
    total_t = sum(r["duration_sec"] for r in results)

    print(f"\n{'='*55}")
    print(f"  📊 執行摘要")
    print(f"{'='*55}")
    print(f"  ✅ 成功：{len(success)}/{len(results)} 個任務")
    print(f"  ❌ 失敗：{len(failed)} 個任務")
    print(f"  ⏱️  總耗時：{total_t:.1f} 秒")
    if failed:
        print(f"\n  失敗詳情：")
        for r in failed:
            print(f"    [{r['analyst_id']}] {r.get('error','unknown')[:80]}")
    print(f"{'='*55}\n")


# ── CLI 入口 ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="PLA 情報分析 — 20人子代理人派遣系統",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python team/sub_agent_runner.py --list
  python team/sub_agent_runner.py --analyst analyst-navy-01 --task "今日PLAN艦艇動態"
  python team/sub_agent_runner.py --batch "055驅逐艦" "殲20 ADIZ" "南海海警"
  python team/sub_agent_runner.py --daily
  python team/sub_agent_runner.py --daily --dry-run
        """
    )
    parser.add_argument("--list",       action="store_true", help="列出所有分析師")
    parser.add_argument("--analyst",    type=str,            help="指定分析師 ID")
    parser.add_argument("--task",       type=str,            help="分析任務描述")
    parser.add_argument("--batch",      nargs="+",           help="批次任務（關鍵字清單，自動路由）")
    parser.add_argument("--daily",      action="store_true", help="掃描 _daily_input/ 執行每日分析")
    parser.add_argument("--date",       type=str,            help="日期字串 YYYYMMDD（預設：今天）")
    parser.add_argument("--dry-run",    action="store_true", help="模擬執行，不實際呼叫 claude")
    parser.add_argument("--parallel",   type=int, default=MAX_PARALLEL, help=f"最大並行數（預設：{MAX_PARALLEL}）")

    args = parser.parse_args()

    if args.list:
        list_analysts()

    elif args.analyst and args.task:
        r = run_analyst(args.analyst, args.task, date_str=args.date, dry_run=args.dry_run)
        print_summary([r])

    elif args.batch:
        results = run_batch(args.batch, date_str=args.date, max_parallel=args.parallel, dry_run=args.dry_run)
        print_summary(results)

    elif args.daily:
        results = run_daily(date_str=args.date, dry_run=args.dry_run)
        print_summary(results)

    else:
        parser.print_help()
