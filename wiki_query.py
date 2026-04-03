"""
wiki_query.py — 知識庫問答查詢工具

功能：
透過 LLM (Claude/Grok) 直接對你的軍事情報 Wiki 進行自然語言問答。
系統會自動載入索引、時間線與概念文章作為背景知識來回答你的問題。

用法：
    python wiki_query.py "請總結最近關於055型驅逐艦的動態"
    python wiki_query.py "東沙群島的灰色地帶作戰有什麼新進展？"
"""

import os
import sys
import argparse
from pathlib import Path

# 確保輸出支援 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# ============= 路徑設定 =============
WORKSPACE = Path(r"C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新")
WIKI_DIR = WORKSPACE / "wiki"
ENV_FILE = WORKSPACE / ".env"

# ============= 載入金鑰 =============
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
    # 根據指示，此系統（Antigravity負責範圍）主要依賴 Grok
    if GROK_KEY:
        from openai import OpenAI
        return "grok", OpenAI(api_key=GROK_KEY, base_url="https://api.x.ai/v1")
    elif ANTHROPIC_KEY:
        import anthropic
        return "anthropic", anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    else:
        print("❌ 沒有可用的 API Key (請檢查 .env 檔案)")
        sys.exit(1)

def llm_chat(prompt: str, system: str = "") -> str:
    backend, client = get_llm_client()
    if backend == "anthropic":
        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    else:
        resp = client.chat.completions.create(
            model="grok-3",
            max_tokens=4000,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ]
        )
        return resp.choices[0].message.content

# ============= 讀取背景知識 =============
def read_wiki_context(query: str) -> str:
    context_blocks = []
    
    # 1. 必讀：全域索引與時間線
    try:
        index_text = (WIKI_DIR / "_index.md").read_text(encoding="utf-8")
        timeline_text = (WIKI_DIR / "_timeline.md").read_text(encoding="utf-8")
        context_blocks.append(f"--- 全域索引 ---\n{index_text}")
        context_blocks.append(f"--- 時間線 (近兩週) ---\n{timeline_text[:3000]}") # 取部分時間線即可
    except Exception as e:
        print(f"警告：讀取基礎索引失敗 ({e})")

    # 2. 自動匹配：讀取所有概念文章
    # 現在 LLM Context window 很大，不到 20 個 concept 全塞進去也沒問題
    # 這就是暴力但極有效的 personal RAG
    concepts_dir = WIKI_DIR / "concepts"
    if concepts_dir.exists():
        for file in concepts_dir.glob("*.md"):
            try:
                text = file.read_text(encoding="utf-8")
                # 如果該概念關鍵字有出現在使用者的問題中，我們就把這篇概念的內容權重放高 (全讀)
                # 為了避免 token 爆炸，這邊把所有概念文章的前 1500 字元放入 context
                context_blocks.append(f"--- 知識庫文章：{file.name} ---\n{text[:1500]}")
            except:
                pass
                
    return "\n\n".join(context_blocks)

# ============= 主程序 =============
def query_wiki(question: str):
    print("🔍 正在翻閱情報知識庫...")
    context = read_wiki_context(question)
    
    system_prompt = """你是台灣國防與安全研究的專屬 AI 助理。
使用者的問題將針對「中共軍事動態情報知識庫」進行提問。
我會把知識庫中目前的索引、時間線以及概念文章內容提供給你作為「背景知識」。

【回答原則】：
1. 你的回答必須**完全基於我提供的背景知識**。如果知識庫裡沒有相關資訊，請誠實說「目前的知識庫中沒有相關紀錄」。
2. 請使用專業、冷靜的情報分析口吻。
3. 如果引用了特定事件，請標示出日期（例如：根據 2026-04-03 的紀錄）。
4. 全部使用繁體中文。
"""
    
    user_prompt = f"""以下是從知識庫中提取的背景資料：

========================================
{context}
========================================

請基於上述資料，回答以下問題：
🗣️ {question}
"""
    
    print("🧠 正在生成分析結果...\n")
    print("=" * 60)
    try:
        response = llm_chat(user_prompt, system=system_prompt)
        print(response)
    except Exception as e:
        print(f"❌ 查詢失敗: {e}")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="中共軍事動態情報知識庫查詢工具")
    parser.add_argument("question", nargs="?", help="你想問知識庫的問題？", default="")
    args = parser.parse_args()

    # 若未提供參數，則啟動互動模式
    if not args.question:
        print("💡 歡迎來到情報知識庫查詢系統！(輸入 'exit' 或 'quit' 離開)")
        while True:
            try:
                q = input("\n你想問什麼問題？\n> ")
                if q.lower() in ['exit', 'quit', 'q']:
                    break
                if q.strip():
                    query_wiki(q)
            except KeyboardInterrupt:
                break
    else:
        query_wiki(args.question)
