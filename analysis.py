import os
import sys
import json
from datetime import datetime
from pathlib import Path
import anthropic

# 修正 Windows 終端編碼問題
sys.stdout.reconfigure(encoding='utf-8')

# ============= 設定 =============
WORKSPACE = r"C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新"

# 使用環境變數讀取 API Key（更安全）
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not API_KEY:
    print("❌ 請設定環境變數 ANTHROPIC_API_KEY")
    print("   Windows CMD:  set ANTHROPIC_API_KEY=sk-ant-...")
    print("   PowerShell:   $env:ANTHROPIC_API_KEY='sk-ant-...'")
    exit(1)

# 建立資料夾路徑
INPUT_DIR = Path(WORKSPACE) / "_daily_input"
OUTPUT_DIR = Path(WORKSPACE) / "_daily_output"
ARCHIVE_DIR = Path(WORKSPACE) / "_archive"

# ============= 初始化 =============
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

client = anthropic.Anthropic(api_key=API_KEY)

# ============= 核心分析函數 =============
def analyze_x_post(x_content: str) -> dict:
    """
    分析 X 貼文，產出：
    1. 原始摘要 (中英對照)
    2. 分析稿 + 政策建議
    3. 引用註釋
    """

    prompt = f"""你是台灣國防與安全研究的專家分析師。

以下是一篇 X 貼文，內容涉及中共軍事動態：

---
{x_content}
---

請進行以下分析工作（全部用繁體中文）：

1. **原始摘要（中英對照表格）**
   - 左欄：英文原文（逐句）
   - 右欄：繁體中文翻譯

2. **核心分析**（300-500 字）
   - 這份報告的關鍵發現是什麼？
   - 對台灣防衛的潛在影響是什麼？
   - 與過往中共軍事發展的關聯？

3. **政策建議清單**
   - 針對國防部門
   - 針對民防規劃
   - 針對國際協調

4. **引用註釋格式**
   - 按 Chicago 格式（帶自動編號）
   - 包含原 URL、日期、來源機構

輸出格式必須是 Markdown，包含清晰的標題層級。
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return {
        "analysis": message.content[0].text,
        "timestamp": datetime.now().isoformat()
    }


# ============= 主程序 =============
def main():
    # Step 0: 嘗試自動讀取 Gmail（Grok 郵件）
    try:
        from gmail_reader import GrokEmailReader
        reader = GrokEmailReader()
        gmail_files = reader.run()
        if gmail_files:
            print(f"📬 Gmail 自動讀取: {len(gmail_files)} 封新郵件")
    except FileNotFoundError:
        print("⚠️ Gmail 認證未設定，使用手動輸入模式")
    except ImportError:
        print("⚠️ gmail_reader 模組未安裝，使用手動輸入模式")
    except Exception as e:
        print(f"⚠️ Gmail 讀取失敗，使用手動輸入模式: {e}")

    # 掃描輸入資料夾（含手動 + Gmail 自動讀取的檔案）
    input_files = list(INPUT_DIR.glob("*.txt"))

    if not input_files:
        print("❌ 沒有找到輸入檔案")
        return

    print(f"✅ 找到 {len(input_files)} 個輸入檔案")
    generated_reports = []

    for input_file in input_files:
        print(f"\n📄 處理: {input_file.name}")

        # 讀取輸入
        with open(input_file, 'r', encoding='utf-8') as f:
            x_content = f.read()

        # 分析
        try:
            result = analyze_x_post(x_content)
            analysis = result["analysis"]

            # 生成輸出檔案名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = input_file.stem

            # 輸出: 完整分析稿
            output_file = OUTPUT_DIR / f"{timestamp}_{base_name}_analysis.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# 中共軍事動態分析\n\n")
                f.write(f"**日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**來源檔案**: {input_file.name}\n\n")
                f.write("---\n\n")
                f.write(analysis)

            print(f"✅ 已生成: {output_file.name}")
            generated_reports.append(output_file)

            # 移動到歸檔
            archive_file = ARCHIVE_DIR / f"{timestamp}_{input_file.name}"
            input_file.rename(archive_file)
            print(f"📁 已歸檔: {archive_file.name}")

        except Exception as e:
            print(f"❌ 分析失敗: {str(e)}")

    # Step 3: 發送通知（Email + LINE）
    if generated_reports:
        try:
            from notifier import Notifier
            notifier = Notifier()
            print(f"\n📤 發送通知...")

            for report in generated_reports:
                result = notifier.notify_report(report)
                if result['email']:
                    print(f"  📧 Email 已發送: {report.name}")
                if result['line']:
                    print(f"  📱 LINE 已推送: {report.name}")

            print(f"✅ 通知發送完成")
        except ImportError:
            print("⚠️ notifier 模組未安裝，跳過通知")
        except Exception as e:
            print(f"⚠️ 通知發送失敗: {e}")


if __name__ == "__main__":
    main()
