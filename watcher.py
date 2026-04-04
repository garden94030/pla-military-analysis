"""
watcher.py — 中共軍事動態分析系統：自動監測觸發器
===================================================
監控 _daily_input/ 與 wiki/raw/ 資料夾，
一旦發現新檔案，立即自動執行 analysis.py。
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

# 修正 Windows 終端編碼
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE = Path(r"C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新")
INPUT_DIR = WORKSPACE / "_daily_input"
RAW_DIR   = WORKSPACE / "wiki" / "raw"
LOG_DIR   = WORKSPACE / "logs"
LOG_FILE  = LOG_DIR / "automation.log"

# 確保目錄存在
LOG_DIR.mkdir(exist_ok=True)

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {message}"
    print(full_msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def get_files_to_process():
    files = []
    # 支援的副檔名 (同 analysis.py)
    EXTS = ["*.txt", "*.pdf", "*.docx", "*.md", "*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp", "*.bmp", "*.jfif"]
    for d in [INPUT_DIR, RAW_DIR]:
        if not d.exists(): continue
        for ext in EXTS:
            files.extend(list(d.glob(ext)))
    return files

def wait_for_file_stable(file_path, wait_seconds=2):
    """確保檔案寫入完成，透過檢查檔案大小是否變動"""
    try:
        last_size = -1
        while True:
            current_size = os.path.getsize(file_path)
            if current_size == last_size:
                break
            last_size = current_size
            time.sleep(wait_seconds)
    except Exception as e:
        log(f"⚠️ 穩定度檢查失敗: {e}")

def run_analysis():
    log("🚀 偵測到新資料，啟動 analysis.py...")
    try:
        # 使用正確的 Python 3.13 路徑，避免與 Inkscape 等環境衝突
        python_exe = r"C:\Users\garde\AppData\Local\Programs\Python\Python313\python.exe"
        result = subprocess.run(
            [python_exe, str(WORKSPACE / "analysis.py")],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        if result.returncode == 0:
            log("✅ Analysis 執行完成。")
            if result.stdout:
                # 打印最後幾行輸出
                lines = result.stdout.strip().splitlines()
                for l in lines[-3:]: log(f"   [Output] {l}")
        else:
            log(f"❌ Analysis 執行失敗 (Code {result.returncode})")
            log(f"   [Error] {result.stderr}")
    except Exception as e:
        log(f"❌ 執行過程發生異常: {e}")

def main():
    log("=" * 50)
    log("PLA Intelligence Watcher 已啟動")
    log(f"監控目錄 1: {INPUT_DIR}")
    log(f"監控目錄 2: {RAW_DIR}")
    log("=" * 50)

    try:
        while True:
            files = get_files_to_process()
            if files:
                log(f"✨ 發現 {len(files)} 個待處理檔案。")
                # 隨便選第一個檔案做穩定性檢查
                wait_for_file_stable(files[0])
                # 執行分析
                run_analysis()
                # 休息一下，避免連續觸發 (analysis 完畢後檔案會被 archive)
                time.sleep(10)
            else:
                # 無檔案，閒置
                time.sleep(5)
    except KeyboardInterrupt:
        log("🛑 Watcher 已手動停止。")
    except Exception as e:
        log(f"💥 Watcher 發生嚴重錯誤: {e}")

if __name__ == "__main__":
    main()
