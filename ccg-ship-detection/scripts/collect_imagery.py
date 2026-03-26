#!/usr/bin/env python3
"""
CCG Ship Detection - Satellite Imagery Collection Script
中共海警船偵測 - 衛星影像蒐集腳本

Collects satellite imagery from various providers for regions of interest
where CCG vessels are known to operate.
"""

import json
import os
import sys
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "datasets" / "raw"


def load_config(config_path: str) -> dict:
    """Load collection source configuration."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_image_id(source: str, region: str, timestamp: str) -> str:
    """Generate a unique image ID based on source, region, and timestamp."""
    raw = f"{source}_{region}_{timestamp}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


class SentinelCollector:
    """Collect imagery from ESA Copernicus Sentinel satellites."""

    def __init__(self, config: dict):
        self.api_endpoint = config["api_endpoint"]
        self.resolution = config["resolution_m"]
        self.name = config["name"]

    def search(self, bbox: list, start_date: str, end_date: str,
               cloud_cover_max: float = 20.0) -> list:
        """
        Search for available imagery in the given bounding box and date range.

        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            start_date: ISO format date string
            end_date: ISO format date string
            cloud_cover_max: Maximum cloud cover percentage

        Returns:
            List of available image metadata dicts
        """
        logger.info(
            f"[{self.name}] Searching bbox={bbox}, "
            f"dates={start_date} to {end_date}, "
            f"cloud_cover<={cloud_cover_max}%"
        )

        # Copernicus Open Access Hub query format
        # In production, use sentinelsat or cdse-api library
        footprint = (
            f"POLYGON(("
            f"{bbox[0]} {bbox[1]},"
            f"{bbox[2]} {bbox[1]},"
            f"{bbox[2]} {bbox[3]},"
            f"{bbox[0]} {bbox[3]},"
            f"{bbox[0]} {bbox[1]}"
            f"))"
        )

        query_params = {
            "platformname": "Sentinel-2" if "2" in self.name else "Sentinel-1",
            "footprint": f'"Intersects({footprint})"',
            "beginPosition": f"[{start_date}T00:00:00.000Z TO {end_date}T23:59:59.999Z]",
            "cloudcoverpercentage": f"[0 TO {cloud_cover_max}]",
        }

        logger.info(f"[{self.name}] Query constructed. "
                     "Connect to Copernicus API to execute.")

        # Placeholder - implement with sentinelsat:
        # from sentinelsat import SentinelAPI
        # api = SentinelAPI(user, password, self.api_endpoint)
        # products = api.query(footprint, date=(start_date, end_date), ...)
        return []

    def download(self, product_id: str, output_dir: Path) -> Path:
        """Download a specific image product."""
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{self.name}_{product_id}.tif"
        logger.info(f"[{self.name}] Downloading {product_id} -> {output_path}")
        # Placeholder - implement actual download
        return output_path


class PlanetCollector:
    """Collect imagery from Planet Labs."""

    def __init__(self, config: dict):
        self.api_endpoint = config["api_endpoint"]
        self.api_key = os.environ.get("PLANET_API_KEY", "")
        self.name = config["name"]

    def search(self, bbox: list, start_date: str, end_date: str) -> list:
        """Search Planet API for available imagery."""
        logger.info(f"[{self.name}] Searching bbox={bbox}")

        if not self.api_key:
            logger.warning(f"[{self.name}] PLANET_API_KEY not set. Skipping.")
            return []

        # Planet Data API v1 search filter
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
                }
            ]
        }

        logger.info(f"[{self.name}] Search filter constructed. "
                     "Connect to Planet API to execute.")
        # Placeholder - implement with planet SDK:
        # import planet
        # async with planet.Session(auth=planet.Auth.from_key(self.api_key)) as sess:
        #     cl = sess.client('data')
        #     items = cl.search(['PSScene'], search_filter)
        return []


class SkyFiCollector:
    """Collect imagery via SkyFi aggregation platform."""

    def __init__(self, config: dict):
        self.api_endpoint = config["api_endpoint"]
        self.api_key = os.environ.get("SKYFI_API_KEY", "")
        self.name = config["name"]

    def search(self, bbox: list, start_date: str, end_date: str) -> list:
        """Search SkyFi for available imagery from multiple providers."""
        logger.info(f"[{self.name}] Searching bbox={bbox}")

        if not self.api_key:
            logger.warning(f"[{self.name}] SKYFI_API_KEY not set. Skipping.")
            return []

        # SkyFi API search
        logger.info(f"[{self.name}] Search constructed. "
                     "Connect to SkyFi API to execute.")
        return []


COLLECTOR_MAP = {
    "sentinel1": SentinelCollector,
    "sentinel2": SentinelCollector,
    "planet": PlanetCollector,
    "skyfi": SkyFiCollector,
}


def collect_all(config_path: str, days_back: int = 30):
    """
    Main collection pipeline: search all sources for all regions of interest.

    Args:
        config_path: Path to collection_sources.json
        days_back: How many days back to search
    """
    config = load_config(config_path)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    logger.info(f"Collection period: {start_date} to {end_date}")
    logger.info(f"Regions of interest: {len(config['regions_of_interest'])}")

    results_summary = []

    for source_cfg in config["sources"]:
        source_name = source_cfg["name"]
        collector_cls = COLLECTOR_MAP.get(source_name)

        if not collector_cls:
            logger.info(f"No collector implemented for {source_name}. Skipping.")
            continue

        collector = collector_cls(source_cfg)

        for region in config["regions_of_interest"]:
            region_name = region["name"]
            bbox = region["bbox"]
            priority = region.get("priority", "normal")

            logger.info(f"Searching {source_name} for {region_name} "
                        f"(priority: {priority})")

            products = collector.search(bbox, start_date, end_date)

            if products:
                logger.info(f"Found {len(products)} images for {region_name}")
                for product in products:
                    output_dir = RAW_DIR / source_name / region_name.replace(" ", "_")
                    collector.download(product["id"], output_dir)

            results_summary.append({
                "source": source_name,
                "region": region_name,
                "priority": priority,
                "images_found": len(products),
            })

    # Summary report
    logger.info("\n=== Collection Summary ===")
    total = 0
    for r in results_summary:
        logger.info(f"  {r['source']:12s} | {r['region']:30s} | "
                     f"Priority: {r['priority']:8s} | Images: {r['images_found']}")
        total += r["images_found"]
    logger.info(f"  Total images found: {total}")

    return results_summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Collect satellite imagery for CCG ship detection"
    )
    parser.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "configs" / "collection_sources.json"),
        help="Path to collection sources config"
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=30,
        help="Number of days to search back (default: 30)"
    )
    args = parser.parse_args()

    collect_all(args.config, args.days_back)
