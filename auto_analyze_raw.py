"""
auto_analyze_raw.py — wiki/raw/ 自動分析管道
=====================================================
監測 wiki/raw/ 資料夾新檔案，自動觸發分析流程

用法：
  python auto_analyze_raw.py                    # 掃描並分析
  python auto_analyze_raw.py --watch            # 連續監測模式
  python auto_analyze_raw.py --process-file <file>  # 處理單個檔案
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).parent
RAW_DIR = PROJECT_ROOT / "wiki" / "raw"
PROCESSED_LOG = PROJECT_ROOT / "_system" / "raw_processed.json"
DAILY_INPUT = PROJECT_ROOT / "_daily_input"


def load_processed_log():
    """載入已處理檔案記錄"""
    if PROCESSED_LOG.exists():
        try:
            return json.loads(PROCESSED_LOG.read_text(encoding="utf-8"))
        except:
            return {"processed_files": {}, "last_run": None}
    return {"processed_files": {}, "last_run": None}


def save_processed_log(log):
    """保存已處理檔案記錄"""
    PROCESSED_LOG.parent.mkdir(parents=True, exist_ok=True)
    PROCESSED_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_filename_without_extension(file_path):
    """提取檔名（去副檔名）"""
    return Path(file_path).stem


def is_image_or_document(file_path):
    """判斷是否為圖片或文件"""
    image_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
    doc_exts = {".pdf", ".docx", ".txt", ".md"}
    suffix = Path(file_path).suffix.lower()
    return suffix in image_exts or suffix in doc_exts


def scan_raw_directory():
    """掃描 raw 資料夾，返回新檔案列表"""
    if not RAW_DIR.exists():
        print(f"❌ raw 資料夾不存在: {RAW_DIR}")
        return []

    log = load_processed_log()
    processed = log.get("processed_files", {})
    new_files = []

    for file_path in RAW_DIR.iterdir():
        if file_path.is_file() and is_image_or_document(file_path):
            file_key = file_path.name
            
            if file_key not in processed:
                new_files.append(file_path)
                print(f"✨ 發現新檔案: {file_path.name}")

    return new_files


def create_analysis_task_from_file(file_path):
    """從 raw 檔案建立分析任務，移至 _daily_input"""
    filename = file_path.name
    stem = extract_filename_without_extension(file_path)
    
    # 建立分析任務檔案
    DAILY_INPUT.mkdir(parents=True, exist_ok=True)
    task_file = DAILY_INPUT / f"raw_{stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    # 寫入任務描述
    content = f"""---
title: 【自動轉移】{stem}
type: raw_input
source_file: {filename}
status: pending
date: {datetime.now().isoformat()}
---

## 原始資料來源
- **檔案**: {filename}
- **位置**: wiki/raw/{filename}
- **接收時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 分析待辦
- [ ] 提取地點/關鍵詞
- [ ] 生成初步分析
- [ ] 標記完成狀態

**備註**: 本檔案由自動化系統從 wiki/raw/ 轉移，建議進行進一步的手工審視。
"""
    
    task_file.write_text(content, encoding="utf-8")
    print(f"📝 建立分析任務: {task_file.name}")
    return task_file


def mark_file_processed(file_path):
    """標記檔案為已處理"""
    log = load_processed_log()
    file_key = file_path.name
    
    log["processed_files"][file_key] = {
        "processed_at": datetime.now().isoformat(),
        "file_path": str(file_path),
        "status": "converted_to_daily_input"
    }
    log["last_run"] = datetime.now().isoformat()
    
    save_processed_log(log)
    print(f"✅ 標記已處理: {file_key}")


def print_status_report():
    """打印狀態報告"""
    log = load_processed_log()
    processed_count = len(log.get("processed_files", {}))
    
    print("\n" + "="*60)
    print("  📊 Raw 資料夾自動化處理狀態")
    print("="*60)
    print(f"  已處理檔案數: {processed_count}")
    print(f"  上次執行時間: {log.get('last_run', '未執行')}")
    print(f"  Raw 資料夾路徑: {RAW_DIR}")
    print(f"  Daily Input 路徑: {DAILY_INPUT}")
    print("="*60 + "\n")


def main():
    """主流程"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--watch":
            print("🔄 連續監測模式啟動（未實現，請使用 hot-reload hook）")
            return
        elif sys.argv[1] == "--process-file" and len(sys.argv) > 2:
            file_path = Path(sys.argv[2])
            if file_path.exists():
                create_analysis_task_from_file(file_path)
                mark_file_processed(file_path)
            return
    
    # 預設行為：掃描並處理新檔案
    print("🔍 掃描 wiki/raw/ 新檔案...")
    new_files = scan_raw_directory()
    
    if new_files:
        print(f"\n🚀 發現 {len(new_files)} 個新檔案，正在建立分析任務...")
        for file_path in new_files:
            create_analysis_task_from_file(file_path)
            mark_file_processed(file_path)
        print("\n✨ 所有新檔案已轉移至分析待列隊")
    else:
        print("  → 無新檔案")
    
    print_status_report()


if __name__ == "__main__":
    main()
