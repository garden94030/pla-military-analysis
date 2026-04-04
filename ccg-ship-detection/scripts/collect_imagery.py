#!/usr/bin/env python3
"""
CCG Ship Detection - Satellite Imagery Collection Script
中共海警船偵測 - 衛星影像蒐集腳本

實際連接衛星影像 API 進行搜尋與下載:
- Copernicus Data Space Ecosystem (CDSE): Sentinel-1 SAR / Sentinel-2 光學 (免費)
- Planet Labs: 3m 光學影像 (商業)
- SkyFi: 多源聚合平台 (商業)

使用方式:
  1. 複製 .env.example -> .env 並填入 API 金鑰
  2. pip install -r requirements.txt
  3. python scripts/collect_imagery.py --source sentinel2 --region "Taiwan Strait"
  4. python scripts/collect_imagery.py --source sentinel2 --all-regions
"""

import json
import os
import sys
import time
import hashlib
import logging
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import requests

# 載入 .env 檔案（如果存在）
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "datasets" / "raw"
LOGS_DIR = PROJECT_ROOT / "logs"


def load_config(config_path: str) -> dict:
    """載入蒐集來源設定檔。"""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_filename(name: str) -> str:
    """將區域名稱轉為安全的檔案夾名稱。"""
    return name.replace(" ", "_").replace("/", "-").replace(":", "")


def save_collection_log(results: list, output_dir: Path):
    """儲存蒐集記錄為 JSON。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = output_dir / f"collection_log_{timestamp}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    logger.info(f"蒐集記錄已儲存: {log_path}")
    return log_path


# ============================================================
# Copernicus Data Space Ecosystem (CDSE) - Sentinel-1 / Sentinel-2
# 免費衛星影像平台，取代舊版 scihub
# 註冊: https://dataspace.copernicus.eu/
# ============================================================

class CDSEAuth:
    """CDSE OAuth2 認證管理器。"""

    TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self._token = None
        self._token_expiry = 0

    def get_token(self) -> str:
        """取得或更新 OAuth2 access token。"""
        if self._token and time.time() < self._token_expiry - 60:
            return self._token

        logger.info("[CDSE] 正在取得 access token...")
        resp = requests.post(self.TOKEN_URL, data={
            "client_id": "cdse-public",
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
        })

        if resp.status_code != 200:
            logger.error(f"[CDSE] 認證失敗 (HTTP {resp.status_code}): {resp.text}")
            raise RuntimeError(f"CDSE authentication failed: {resp.status_code}")

        token_data = resp.json()
        self._token = token_data["access_token"]
        self._token_expiry = time.time() + token_data.get("expires_in", 600)
        logger.info("[CDSE] Token 取得成功")
        return self._token


class SentinelCollector:
    """
    透過 CDSE OData API 蒐集 Sentinel-1/Sentinel-2 影像。

    CDSE OData API 文件:
    https://documentation.dataspace.copernicus.eu/APIs/OData.html
    """

    ODATA_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    DOWNLOAD_URL = "https://zipper.dataspace.copernicus.eu/odata/v1/Products"

    def __init__(self, config: dict):
        self.name = config["name"]
        self.resolution = config["resolution_m"]

        username = os.environ.get("CDSE_USERNAME", "")
        password = os.environ.get("CDSE_PASSWORD", "")

        if username and password:
            self.auth = CDSEAuth(username, password)
        else:
            self.auth = None
            logger.warning(
                f"[{self.name}] CDSE_USERNAME / CDSE_PASSWORD 未設定。"
                " 可搜尋但無法下載。"
                " 免費註冊: https://dataspace.copernicus.eu/"
            )

    def _get_collection_name(self) -> str:
        """取得 CDSE collection 名稱。"""
        if "1" in self.name:
            return "SENTINEL-1"
        return "SENTINEL-2"

    def search(self, bbox: list, start_date: str, end_date: str,
               cloud_cover_max: float = 20.0, max_results: int = 20) -> list:
        """
        搜尋 CDSE 目錄中的可用影像。

        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            start_date: 日期字串 (YYYY-MM-DD)
            end_date: 日期字串 (YYYY-MM-DD)
            cloud_cover_max: 最大雲量百分比 (僅 Sentinel-2)
            max_results: 最大回傳筆數

        Returns:
            影像產品元資料清單
        """
        collection = self._get_collection_name()

        # 建立 OData 空間篩選 (用 WKT POLYGON)
        polygon_wkt = (
            f"POLYGON(("
            f"{bbox[0]} {bbox[1]},"
            f"{bbox[2]} {bbox[1]},"
            f"{bbox[2]} {bbox[3]},"
            f"{bbox[0]} {bbox[3]},"
            f"{bbox[0]} {bbox[1]}"
            f"))"
        )

        # OData 查詢篩選條件
        filters = [
            f"Collection/Name eq '{collection}'",
            f"OData.CSC.Intersects(area=geography'SRID=4326;{polygon_wkt}')",
            f"ContentDate/Start gt {start_date}T00:00:00.000Z",
            f"ContentDate/Start lt {end_date}T23:59:59.999Z",
        ]

        # Sentinel-2 加入雲量篩選
        if "SENTINEL-2" in collection:
            filters.append(
                f"Attributes/OData.CSC.DoubleAttribute/any("
                f"att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt {cloud_cover_max})"
            )

        filter_str = " and ".join(filters)

        params = {
            "$filter": filter_str,
            "$top": max_results,
            "$orderby": "ContentDate/Start desc",
        }

        logger.info(
            f"[{self.name}] 搜尋中... 區域={bbox}, "
            f"日期={start_date}~{end_date}, 雲量<={cloud_cover_max}%"
        )

        try:
            resp = requests.get(self.ODATA_URL, params=params, timeout=60)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"[{self.name}] 搜尋 API 錯誤: {e}")
            return []

        data = resp.json()
        products = data.get("value", [])

        results = []
        for p in products:
            results.append({
                "id": p["Id"],
                "name": p["Name"],
                "date": p.get("ContentDate", {}).get("Start", ""),
                "size_mb": round(p.get("ContentLength", 0) / 1024 / 1024, 1),
                "online": p.get("Online", True),
                "source": self.name,
            })

        logger.info(f"[{self.name}] 找到 {len(results)} 筆影像產品")

        for r in results[:5]:
            logger.info(f"  - {r['name']} | {r['date'][:10]} | {r['size_mb']}MB")
        if len(results) > 5:
            logger.info(f"  ... 以及另外 {len(results)-5} 筆")

        return results

    def download(self, product: dict, output_dir: Path) -> Path:
        """
        下載指定的影像產品。

        Args:
            product: search() 回傳的產品元資料
            output_dir: 輸出資料夾

        Returns:
            下載檔案的路徑
        """
        if not self.auth:
            logger.error(
                f"[{self.name}] 無法下載: CDSE 認證未設定。"
                " 請在 .env 中設定 CDSE_USERNAME 和 CDSE_PASSWORD"
            )
            return None

        output_dir.mkdir(parents=True, exist_ok=True)
        product_id = product["id"]
        product_name = product["name"]
        output_path = output_dir / f"{product_name}.zip"

        # 若已下載則跳過
        if output_path.exists():
            logger.info(f"[{self.name}] 已存在，跳過: {output_path.name}")
            return output_path

        token = self.auth.get_token()
        download_url = f"{self.DOWNLOAD_URL}({product_id})/$value"

        logger.info(f"[{self.name}] 下載中: {product_name} ({product['size_mb']}MB)")

        try:
            resp = requests.get(
                download_url,
                headers={"Authorization": f"Bearer {token}"},
                stream=True,
                timeout=300,
            )
            resp.raise_for_status()

            total = int(resp.headers.get("content-length", 0))
            downloaded = 0

            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0 and downloaded % (10 * 1024 * 1024) < 8192:
                        pct = downloaded / total * 100
                        logger.info(f"  進度: {pct:.0f}% ({downloaded//1024//1024}MB / {total//1024//1024}MB)")

            logger.info(f"[{self.name}] 下載完成: {output_path}")

            # 自動解壓縮
            self._extract_if_zip(output_path, output_dir)

            return output_path

        except requests.RequestException as e:
            logger.error(f"[{self.name}] 下載失敗: {e}")
            if output_path.exists():
                output_path.unlink()
            return None

    def _extract_if_zip(self, zip_path: Path, output_dir: Path):
        """解壓縮 Sentinel 產品 ZIP 檔。"""
        if not zipfile.is_zipfile(zip_path):
            return
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(output_dir)
            logger.info(f"[{self.name}] 已解壓縮至: {output_dir}")
        except zipfile.BadZipFile as e:
            logger.warning(f"[{self.name}] 解壓縮失敗: {e}")


# ============================================================
# Planet Labs - 3m 光學衛星影像
# https://developers.planet.com/docs/apis/data/
# ============================================================

class PlanetCollector:
    """透過 Planet Data API v2 蒐集影像。"""

    SEARCH_URL = "https://api.planet.com/data/v1/quick-search"
    ORDERS_URL = "https://api.planet.com/compute/ops/orders/v2"

    def __init__(self, config: dict):
        self.name = config["name"]
        self.api_key = os.environ.get("PLANET_API_KEY", "")
        self.session = requests.Session()
        if self.api_key:
            self.session.auth = (self.api_key, "")

    def search(self, bbox: list, start_date: str, end_date: str,
               cloud_cover_max: float = 20.0, max_results: int = 20) -> list:
        """搜尋 Planet 影像目錄。"""
        if not self.api_key:
            logger.warning(
                f"[{self.name}] PLANET_API_KEY 未設定。跳過。"
                " 申請帳號: https://www.planet.com/"
            )
            return []

        search_filter = {
            "type": "AndFilter",
            "config": [
                {
                    "type": "GeometryFilter",
                    "field_name": "geometry",
                    "config": {
                        "type": "Polygon",
                        "coordinates": [[
                            [bbox[0], bbox[1]],
                            [bbox[2], bbox[1]],
                            [bbox[2], bbox[3]],
                            [bbox[0], bbox[3]],
                            [bbox[0], bbox[1]],
                        ]]
                    }
                },
                {
                    "type": "DateRangeFilter",
                    "field_name": "acquired",
                    "config": {
                        "gte": f"{start_date}T00:00:00.000Z",
                        "lte": f"{end_date}T23:59:59.999Z"
                    }
                },
                {
                    "type": "RangeFilter",
                    "field_name": "cloud_cover",
                    "config": {"lte": cloud_cover_max / 100.0}
                }
            ]
        }

        request_body = {
            "item_types": ["PSScene"],
            "filter": search_filter,
        }

        logger.info(f"[{self.name}] 搜尋中... 區域={bbox}")

        try:
            resp = self.session.post(
                self.SEARCH_URL,
                json=request_body,
                timeout=60,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"[{self.name}] 搜尋 API 錯誤: {e}")
            return []

        data = resp.json()
        features = data.get("features", [])[:max_results]

        results = []
        for f in features:
            props = f.get("properties", {})
            results.append({
                "id": f["id"],
                "name": f["id"],
                "date": props.get("acquired", ""),
                "cloud_cover": round(props.get("cloud_cover", 0) * 100, 1),
                "gsd": props.get("gsd", 0),
                "satellite_id": props.get("satellite_id", ""),
                "source": self.name,
            })

        logger.info(f"[{self.name}] 找到 {len(results)} 筆影像")

        for r in results[:5]:
            logger.info(
                f"  - {r['name']} | {r['date'][:10]} | "
                f"雲量={r['cloud_cover']}% | GSD={r['gsd']}m"
            )

        return results

    def download(self, product: dict, output_dir: Path) -> Path:
        """透過 Planet Orders API 下載影像。"""
        if not self.api_key:
            return None

        output_dir.mkdir(parents=True, exist_ok=True)

        # Planet 使用 Orders API 進行下載
        order_request = {
            "name": f"ccg_detection_{product['id']}",
            "products": [
                {
                    "item_ids": [product["id"]],
                    "item_type": "PSScene",
                    "product_bundle": "analytic_udm2",
                }
            ],
        }

        logger.info(f"[{self.name}] 建立下載訂單: {product['id']}")

        try:
            resp = self.session.post(
                self.ORDERS_URL,
                json=order_request,
                timeout=60,
            )
            resp.raise_for_status()
            order = resp.json()
            order_id = order["id"]
            logger.info(f"[{self.name}] 訂單已建立: {order_id}")
            logger.info(f"[{self.name}] 訂單需等待處理完成後再下載。")
            logger.info(f"[{self.name}] 可用 check_planet_order('{order_id}') 查詢狀態")

            # 儲存訂單資訊
            order_log = output_dir / f"planet_order_{order_id}.json"
            with open(order_log, "w") as f:
                json.dump(order, f, indent=2)

            return order_log

        except requests.RequestException as e:
            logger.error(f"[{self.name}] 訂單建立失敗: {e}")
            return None


# ============================================================
# SkyFi - 多源衛星影像聚合平台
# https://docs.skyfi.com/
# ============================================================

class SkyFiCollector:
    """透過 SkyFi API 蒐集影像。"""

    SEARCH_URL = "https://api.skyfi.com/v1/archive/search"

    def __init__(self, config: dict):
        self.name = config["name"]
        self.api_key = os.environ.get("SKYFI_API_KEY", "")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers["X-Skyfi-Api-Key"] = self.api_key

    def search(self, bbox: list, start_date: str, end_date: str,
               cloud_cover_max: float = 20.0, max_results: int = 20) -> list:
        """搜尋 SkyFi 影像檔案庫。"""
        if not self.api_key:
            logger.warning(
                f"[{self.name}] SKYFI_API_KEY 未設定。跳過。"
                " 申請帳號: https://www.skyfi.com/"
            )
            return []

        search_body = {
            "aoi": {
                "type": "Polygon",
                "coordinates": [[
                    [bbox[0], bbox[1]],
                    [bbox[2], bbox[1]],
                    [bbox[2], bbox[3]],
                    [bbox[0], bbox[3]],
                    [bbox[0], bbox[1]],
                ]]
            },
            "startDate": f"{start_date}T00:00:00Z",
            "endDate": f"{end_date}T23:59:59Z",
            "cloudCoverMax": cloud_cover_max,
            "limit": max_results,
        }

        logger.info(f"[{self.name}] 搜尋中... 區域={bbox}")

        try:
            resp = self.session.post(
                self.SEARCH_URL,
                json=search_body,
                timeout=60,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"[{self.name}] 搜尋 API 錯誤: {e}")
            return []

        data = resp.json()
        items = data.get("results", data.get("items", []))[:max_results]

        results = []
        for item in items:
            results.append({
                "id": item.get("id", ""),
                "name": item.get("name", item.get("id", "")),
                "date": item.get("acquisitionDate", item.get("date", "")),
                "resolution": item.get("resolution", ""),
                "provider": item.get("provider", ""),
                "source": self.name,
            })

        logger.info(f"[{self.name}] 找到 {len(results)} 筆影像")
        for r in results[:5]:
            logger.info(f"  - {r['name']} | {r['date'][:10]} | "
                        f"解析度={r['resolution']}m | 來源={r['provider']}")

        return results

    def download(self, product: dict, output_dir: Path) -> Path:
        """透過 SkyFi 下載影像。"""
        if not self.api_key:
            return None

        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[{self.name}] SkyFi 下載需透過平台完成訂購流程。")
        logger.info(f"[{self.name}] 影像 ID: {product['id']}")

        # 儲存搜尋結果供後續訂購
        result_path = output_dir / f"skyfi_result_{product['id']}.json"
        with open(result_path, "w") as f:
            json.dump(product, f, indent=2)
        return result_path


# ============================================================
# 主程式
# ============================================================

COLLECTOR_MAP = {
    "sentinel1": SentinelCollector,
    "sentinel2": SentinelCollector,
    "planet": PlanetCollector,
    "skyfi": SkyFiCollector,
}


def find_source_config(config: dict, source_name: str) -> dict:
    """從設定檔中找到指定來源的設定。"""
    for src in config["sources"]:
        if src["name"] == source_name:
            return src
    return None


def find_region(config: dict, region_name: str) -> dict:
    """從設定檔中找到指定區域（支援部分名稱比對）。"""
    for region in config["regions_of_interest"]:
        if (region_name.lower() in region["name"].lower() or
                region_name in region.get("name_zh", "")):
            return region
    return None


def collect_single(source_name: str, region: dict, config: dict,
                   days_back: int = 30, cloud_max: float = 20.0,
                   download: bool = False, max_results: int = 20) -> dict:
    """
    針對單一來源、單一區域進行搜尋（與可選的下載）。

    Returns:
        蒐集結果摘要 dict
    """
    source_cfg = find_source_config(config, source_name)
    if not source_cfg:
        logger.error(f"找不到來源設定: {source_name}")
        return {"source": source_name, "region": region["name"], "error": "source not found"}

    collector_cls = COLLECTOR_MAP.get(source_name)
    if not collector_cls:
        logger.error(f"尚未實作此來源的蒐集器: {source_name}")
        return {"source": source_name, "region": region["name"], "error": "no collector"}

    collector = collector_cls(source_cfg)

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    region_name = region["name"]
    bbox = region["bbox"]
    priority = region.get("priority", "normal")

    logger.info(f"\n{'='*60}")
    logger.info(f"來源: {source_name} | 區域: {region_name} ({region.get('name_zh', '')})")
    logger.info(f"優先級: {priority} | 日期: {start_date} ~ {end_date}")
    logger.info(f"範圍: {bbox}")
    logger.info(f"{'='*60}")

    products = collector.search(bbox, start_date, end_date, cloud_max, max_results)

    result = {
        "source": source_name,
        "region": region_name,
        "region_zh": region.get("name_zh", ""),
        "priority": priority,
        "bbox": bbox,
        "date_range": f"{start_date} ~ {end_date}",
        "images_found": len(products),
        "products": products,
        "downloaded": [],
    }

    # 下載（如果啟用）
    if download and products:
        output_dir = RAW_DIR / source_name / safe_filename(region_name)
        for product in products:
            dl_path = collector.download(product, output_dir)
            if dl_path:
                result["downloaded"].append(str(dl_path))

    return result


def collect_all_regions(source_name: str, config: dict, days_back: int = 30,
                        cloud_max: float = 20.0, download: bool = False,
                        priority_filter: str = None, max_results: int = 10) -> list:
    """
    針對單一來源，搜尋所有（或指定優先級的）區域。

    Args:
        priority_filter: 只搜尋此優先級的區域 ("critical", "high", "medium")
    """
    results = []
    regions = config["regions_of_interest"]

    if priority_filter:
        regions = [r for r in regions if r.get("priority") == priority_filter]
        logger.info(f"篩選優先級 '{priority_filter}': {len(regions)} 個區域")

    for region in regions:
        result = collect_single(
            source_name, region, config,
            days_back, cloud_max, download, max_results
        )
        results.append(result)

    return results


def print_summary(results: list):
    """印出蒐集結果摘要表格。"""
    logger.info(f"\n{'='*80}")
    logger.info("蒐集結果摘要 (Collection Summary)")
    logger.info(f"{'='*80}")
    logger.info(f"{'來源':<12} | {'區域':<35} | {'優先級':<10} | {'影像數':>6}")
    logger.info(f"{'-'*12}-+-{'-'*35}-+-{'-'*10}-+-{'-'*6}")

    total = 0
    for r in results:
        if "error" in r:
            logger.info(f"{r['source']:<12} | {r['region']:<35} | {'ERROR':<10} | {'-':>6}")
        else:
            logger.info(
                f"{r['source']:<12} | {r['region']:<35} | "
                f"{r['priority']:<10} | {r['images_found']:>6}"
            )
            total += r["images_found"]

    logger.info(f"{'-'*12}-+-{'-'*35}-+-{'-'*10}-+-{'-'*6}")
    logger.info(f"{'合計':<12} | {'':<35} | {'':<10} | {total:>6}")

    if total == 0:
        logger.info("\n提示: 若搜尋結果為 0，請確認:")
        logger.info("  1. API 金鑰已正確設定 (.env 檔案)")
        logger.info("  2. 搜尋日期範圍內有可用影像")
        logger.info("  3. 雲量篩選條件不過於嚴格 (嘗試 --cloud-max 50)")


def check_api_status():
    """檢查各 API 連線狀態。"""
    logger.info("\n=== API 連線狀態檢查 ===\n")

    # CDSE
    cdse_user = os.environ.get("CDSE_USERNAME", "")
    cdse_pass = os.environ.get("CDSE_PASSWORD", "")
    if cdse_user and cdse_pass:
        try:
            auth = CDSEAuth(cdse_user, cdse_pass)
            auth.get_token()
            logger.info("  [CDSE Sentinel] ✓ 認證成功 (免費)")
        except Exception as e:
            logger.info(f"  [CDSE Sentinel] ✗ 認證失敗: {e}")
    else:
        logger.info("  [CDSE Sentinel] — 未設定 (免費註冊: https://dataspace.copernicus.eu/)")

    # Planet
    planet_key = os.environ.get("PLANET_API_KEY", "")
    if planet_key:
        try:
            resp = requests.get(
                "https://api.planet.com/data/v1",
                auth=(planet_key, ""),
                timeout=10,
            )
            if resp.status_code == 200:
                logger.info("  [Planet Labs]   ✓ API 金鑰有效 (商業)")
            else:
                logger.info(f"  [Planet Labs]   ✗ API 回應 {resp.status_code}")
        except Exception as e:
            logger.info(f"  [Planet Labs]   ✗ 連線失敗: {e}")
    else:
        logger.info("  [Planet Labs]   — 未設定 (商業: https://www.planet.com/)")

    # SkyFi
    skyfi_key = os.environ.get("SKYFI_API_KEY", "")
    if skyfi_key:
        logger.info("  [SkyFi]         ✓ API 金鑰已設定 (商業)")
    else:
        logger.info("  [SkyFi]         — 未設定 (商業: https://www.skyfi.com/)")

    logger.info("")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="CCG 船舶偵測 - 衛星影像蒐集工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 檢查 API 連線狀態
  python scripts/collect_imagery.py --check

  # 搜尋台灣海峽近 30 天的 Sentinel-2 影像
  python scripts/collect_imagery.py --source sentinel2 --region "Taiwan Strait"

  # 搜尋所有 critical 優先級區域
  python scripts/collect_imagery.py --source sentinel2 --all-regions --priority critical

  # 搜尋並下載 (需要 API 金鑰)
  python scripts/collect_imagery.py --source sentinel2 --region "Senkaku" --download

  # 搜尋 Planet 影像 (需要 PLANET_API_KEY)
  python scripts/collect_imagery.py --source planet --region "Scarborough Shoal" --days-back 7

  # 搜尋所有來源的所有區域
  python scripts/collect_imagery.py --source all --all-regions
        """
    )
    parser.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "configs" / "collection_sources.json"),
        help="設定檔路徑 (預設: configs/collection_sources.json)"
    )
    parser.add_argument(
        "--source",
        choices=["sentinel1", "sentinel2", "planet", "skyfi", "all"],
        default="sentinel2",
        help="影像來源 (預設: sentinel2)"
    )
    parser.add_argument(
        "--region",
        help="搜尋區域名稱（支援部分比對，如 'Taiwan' 或 '台灣'）"
    )
    parser.add_argument(
        "--all-regions",
        action="store_true",
        help="搜尋所有關注區域"
    )
    parser.add_argument(
        "--priority",
        choices=["critical", "high", "medium"],
        help="只搜尋指定優先級的區域"
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=30,
        help="搜尋回溯天數 (預設: 30)"
    )
    parser.add_argument(
        "--cloud-max",
        type=float,
        default=20.0,
        help="最大雲量百分比 (預設: 20.0)"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=20,
        help="每個區域最大搜尋結果數 (預設: 20)"
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="搜尋後自動下載影像"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="檢查 API 連線狀態"
    )

    args = parser.parse_args()
    config = load_config(args.config)

    # API 狀態檢查
    if args.check:
        check_api_status()
        sys.exit(0)

    # 決定要搜尋的來源
    sources = (
        ["sentinel1", "sentinel2", "planet", "skyfi"]
        if args.source == "all"
        else [args.source]
    )

    all_results = []

    for source in sources:
        if args.all_regions:
            results = collect_all_regions(
                source, config, args.days_back, args.cloud_max,
                args.download, args.priority, args.max_results
            )
            all_results.extend(results)

        elif args.region:
            region = find_region(config, args.region)
            if not region:
                logger.error(f"找不到區域: '{args.region}'")
                logger.info("可用區域:")
                for r in config["regions_of_interest"]:
                    logger.info(f"  - {r['name']} ({r.get('name_zh', '')})")
                sys.exit(1)

            result = collect_single(
                source, region, config,
                args.days_back, args.cloud_max,
                args.download, args.max_results
            )
            all_results.append(result)

        else:
            parser.error("請指定 --region 或 --all-regions")

    # 印出摘要
    print_summary(all_results)

    # 儲存記錄
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    save_collection_log(all_results, LOGS_DIR)
