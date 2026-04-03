import os
import sys
import json
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from team.team_router import route_topic

# 修正 Windows 終端編碼問題
sys.stdout.reconfigure(encoding='utf-8')

# ============= 路徑設定 =============
WORKSPACE = r"C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新"
ENV_FILE  = Path(WORKSPACE) / ".env"

# ── 從 .env 讀取設定 ──────────────────────────────────────
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

ANTHROPIC_KEY = _cfg.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
GROK_KEY      = _cfg.get("GROK_API_KEY")      or os.environ.get("GROK_API_KEY", "")

# ── 自動選擇 API 後端 ─────────────────────────────────────
if ANTHROPIC_KEY:
    API_BACKEND = "anthropic"
    try:
        import anthropic as _anthropic_sdk
        client = _anthropic_sdk.Anthropic(api_key=ANTHROPIC_KEY)
    except ImportError:
        print("❌ 請安裝 anthropic 套件：pip install anthropic")
        sys.exit(1)
    print(f"✅ 使用 Claude (Anthropic)  — Key 前10碼：{ANTHROPIC_KEY[:10]}...")
elif GROK_KEY:
    API_BACKEND = "grok"
    try:
        from openai import OpenAI as _OpenAI
        client = _OpenAI(api_key=GROK_KEY, base_url="https://api.x.ai/v1")
    except ImportError:
        print("❌ 請安裝 openai 套件：pip install openai")
        sys.exit(1)
    print(f"✅ 使用 Grok (x.ai)         — Key 前10碼：{GROK_KEY[:10]}...")
else:
    print("❌ 找不到任何可用的 API Key！")
    sys.exit(1)

# 建立資料夾路徑
INPUT_DIR    = Path(WORKSPACE) / "_daily_input"
OBSIDIAN_RAW = Path(WORKSPACE) / "wiki" / "raw"
OUTPUT_DIR   = Path(WORKSPACE) / "_daily_output"
ARCHIVE_DIR  = Path(WORKSPACE) / "_archive"
GEO_DIR      = Path(WORKSPACE) / "_geo_output"
SYSTEM_DIR   = Path(WORKSPACE) / "_system"
WIKI_DIR     = Path(WORKSPACE) / "wiki"

# ============= 初始化 =============
for d in [INPUT_DIR, OBSIDIAN_RAW, OUTPUT_DIR, ARCHIVE_DIR, GEO_DIR, SYSTEM_DIR]:
    os.makedirs(d, exist_ok=True)

# ============= 系統狀態管理 =============
def get_next_issue_id() -> int:
    """取得並更新全域議題編號"""
    counter_file = SYSTEM_DIR / "issue_counter.json"
    data = {"current_issue_id": 1, "last_updated": datetime.now().strftime("%Y-%m-%d")}
    
    if counter_file.exists():
        try:
            data = json.loads(counter_file.read_text(encoding="utf-8"))
        except:
            pass
            
    issue_id = data.get("current_issue_id", 1)
    data["current_issue_id"] = issue_id + 1
    data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    counter_file.write_text(json.dumps(data, indent=4), encoding="utf-8")
    return issue_id

# ============= Wiki 知識庫上下文 =============
def load_wiki_context(x_content: str) -> str:
    """從 wiki 知識庫載入相關上下文，注入分析 prompt"""
    context_parts = []
    index_file = WIKI_DIR / "_index.md"
    if index_file.exists():
        idx_text = index_file.read_text(encoding="utf-8")
        if "## 📌 概念文章索引" in idx_text:
            start = idx_text.index("## 📌 概念文章索引")
            end = idx_text.index("---", start + 10) if "---" in idx_text[start + 10:] else start + 2000
            context_parts.append(idx_text[start:start + end - start][:1500])
    
    concepts_dir = WIKI_DIR / "concepts"
    if concepts_dir.exists():
        for concept_file in concepts_dir.glob("*.md"):
            concept_name = concept_file.stem
            keywords = concept_name.replace("與", " ").replace("及", " ").replace("和", " ").split()
            if any(kw in x_content for kw in keywords if len(kw) >= 2):
                try:
                    content = concept_file.read_text(encoding="utf-8")
                    context_parts.append(f"--- 已知概念：{concept_name} ---\n{content[:400]}")
                except:
                    pass
    return "\n\n".join(context_parts[:5]) if context_parts else ""

# ============= 核心分析函數 =============
def analyze_x_post(x_content: str) -> dict:
    wiki_context = load_wiki_context(x_content)
    wiki_section = f"\n⚠️ 知識庫背景：\n{wiki_context}\n" if wiki_context else ""
    
    prompt = f"""你是台灣國防專家。分析以下情資：
{wiki_section}
{x_content}

### 格式範本：
# 綜合分析報告
## 一、執行摘要
## 二、當日重點事件摘要
### 事件一：...
## 三、核心分析
### 3.1 戰略意圖
### 3.2 歷史案例關聯
## 四、政策建議
## 五、引用文獻 (Chicago)
## 六、相關議題深度清單
"""
    system_msg = "你是資深軍事分析師。"
    if API_BACKEND == "anthropic":
        message = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=3000, system=system_msg,
            messages=[{"role": "user", "content": prompt}]
        )
        text = message.content[0].text
    else:
        response = client.chat.completions.create(
            model="grok-3", max_tokens=3000,
            messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": prompt}]
        )
        text = response.choices[0].message.content
    return {"analysis": text, "timestamp": datetime.now().isoformat()}

def get_expert_review(report_text: str, analyst: dict) -> str:
    system_msg = analyst.get("system_prompt", "你是資深軍事分析師。")
    prompt = f"請對這份報告進行專家複審：\n\n{report_text}\n\n請以『### 🖋️ 專家評核意見：{analyst['name']}』開頭。"
    if API_BACKEND == "anthropic":
        message = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=2000, system=system_msg,
            messages=[{"role": "user", "content": prompt}]
        )
        review = message.content[0].text
    else:
        response = client.chat.completions.create(
            model="grok-3", max_tokens=2000,
            messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": prompt}]
        )
        review = response.choices[0].message.content
    return review

# ============= GIS 處理 =============
def extract_geo_points(report_text: str) -> list:
    prompt = f"""從中提取地點座標。具備數值座標才輸出 JSON。
1. **格式**：JSON 陣列。
2. **座標**：若文中無座標但為關鍵基地（如 906, 葫蘆島），請依知識庫補全，否則跳過。
3. **禁止**：嚴禁輸出 "lon": "None"。

內容：
{report_text}
"""
    if API_BACKEND == "anthropic":
        res_text = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        ).content[0].text
    else:
        res_text = client.chat.completions.create(
            model="grok-3", messages=[{"role": "user", "content": prompt}]
        ).choices[0].message.content
    try:
        match = re.search(r"\[.*\]", res_text, re.S)
        return json.loads(match.group(0)) if match else []
    except:
        return []

def generate_kml_file(geo_points: list, output_path: Path):
    if not geo_points: return None
    kml = ET.Element('kml', xmlns="http://www.opengis.net/kml/2.2")
    doc = ET.SubElement(kml, 'Document')
    ET.SubElement(doc, 'name').text = f"PLA_{datetime.now().strftime('%Y%m%d')}"
    for pt in geo_points:
        try:
            lon, lat = float(pt.get('lon')), float(pt.get('lat'))
            if abs(lon) < 0.1 and abs(lat) < 0.1: continue
            pm = ET.SubElement(doc, 'Placemark')
            ET.SubElement(pm, 'name').text = pt.get('name', '地點')
            ET.SubElement(pm, 'description').text = pt.get('desc', '')
            ET.SubElement(ET.SubElement(pm, 'Point'), 'coordinates').text = f"{lon},{lat},0"
        except: continue
    ET.ElementTree(kml).write(output_path, encoding='utf-8', xml_declaration=True)
    return output_path

# ============= 主程序 =============
def main():
    try:
        from gmail_reader import GrokEmailReader
        GrokEmailReader().run()
    except: pass

    # 掃描 Obsidian raw 與 _daily_input
    input_files = []
    for d in [INPUT_DIR, OBSIDIAN_RAW]:
        for ext in ["*.txt", "*.pdf", "*.docx", "*.md"]:
            input_files.extend(list(d.glob(ext)))

    if not input_files:
        print("ℹ️ 無待處理檔案。")
        return

    all_content = ""
    for f_path in input_files:
        print(f"📄 讀取: {f_path.name}")
        try:
            if f_path.suffix.lower() == '.pdf':
                import PyPDF2
                with open(f_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    all_content += "\n".join([p.extract_text() for p in reader.pages])
            elif f_path.suffix.lower() in ['.docx', '.doc']:
                from docx import Document
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                    shutil.copy2(f_path, tmp.name)
                    doc = Document(tmp.name)
                    all_content += "\n".join([p.text for p in doc.paragraphs])
                os.remove(tmp.name)
            else:
                all_content += f_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"⚠️ 讀起錯誤: {e}")

    result = analyze_x_post(all_content)
    analysis = result["analysis"]
    topic_title = "軍事動態分析"
    tm = re.search(r"^# (.*)", analysis, re.M)
    if tm: topic_title = tm.group(1).strip()
    
    analyst = route_topic(topic_title)
    final_report = analysis + "\n\n" + get_expert_review(analysis, analyst)
    
    issue_id = get_next_issue_id()
    folder_name = f"{datetime.now().strftime('%Y%m%d')}_議題{issue_id}_{re.sub(r'[<>:\"/\\\\|?*]', '_', topic_title)}"
    target_dir = OUTPUT_DIR / folder_name
    os.makedirs(target_dir, exist_ok=True)
    
    rep_path = target_dir / f"{datetime.now().strftime('%H%M%S')}_報告.md"
    rep_path.write_text(f"---\nissue_id: {issue_id}\nreviewer: @{analyst['github']}\n---\n\n{final_report}", encoding="utf-8")
    
    # GIS
    geo = extract_geo_points(final_report)
    if geo:
        kml_path = target_dir / "地理動態.kml"
        generate_kml_file(geo, kml_path)
        shutil.copy2(kml_path, GEO_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_動態.kml")
        print(f"🌍 KML 已生成")

    # 歸檔
    for f in input_files:
        shutil.move(str(f), str(ARCHIVE_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{f.name}"))
    
    print(f"✅ 完成！報告存於: {folder_name}")
    
    # 啟動 Wiki 編譯
    try:
        subprocess.run([sys.executable, "wiki_compiler.py", "--team-sync"], check=True)
    except: pass

if __name__ == "__main__":
    import subprocess
    main()
