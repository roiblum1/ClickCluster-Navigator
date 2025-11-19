"""
Background service to sync data from VLAN Manager API.
"""
import asyncio
import httpx
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import logging
from src.config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
CACHE_FILE = Path(__file__).parent.parent.parent / "data" / "vlan_cache.json"


class VLANSyncService:
    """Service to sync VLAN Manager data with local storage."""

    def __init__(self):
        self.cache_file = CACHE_FILE
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.is_running = False

    async def fetch_allocated_segments(self) -> List[Dict]:
        """Fetch only allocated segments from VLAN Manager API."""
        try:
            vlan_url = config.vlan_manager_url
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{vlan_url}/api/segments",
                    params={"allocated": True}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch allocated segments: {e}")
            return []

    async def fetch_sites(self) -> List[str]:
        """Fetch available sites from VLAN Manager API."""
        try:
            vlan_url = config.vlan_manager_url
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{vlan_url}/api/sites")
                response.raise_for_status()
                data = response.json()
                return data.get("sites", [])
        except Exception as e:
            logger.error(f"Failed to fetch sites: {e}")
            return []

    def transform_to_clusters(self, segments: List[Dict]) -> Dict:
        """
        Transform VLAN segments to cluster data structure.
        Groups segments by cluster_name and site.
        Uses composite key (cluster_name, site) to allow duplicate cluster names across different sites.
        Handles comma-separated cluster names (when multiple clusters share a segment).
        """
        clusters_by_key = {}

        for segment in segments:
            cluster_name_raw = segment.get("cluster_name")
            site = segment.get("site")
            segment_cidr = segment.get("segment")

            # Skip segments without cluster allocation
            if not cluster_name_raw or not site or not segment_cidr:
                continue

            # Skip released segments
            if segment.get("released", False):
                continue

            # Handle comma-separated cluster names (e.g., "ocp4-roi,ocp4-roi2")
            # Split by comma and process each cluster separately
            cluster_names = [name.strip() for name in cluster_name_raw.split(",")]

            for cluster_name in cluster_names:
                # Skip empty names
                if not cluster_name:
                    continue

                # Use composite key (cluster_name, site) to allow duplicate names across sites
                cluster_key = f"{cluster_name}@{site}"

                # Initialize cluster entry if not exists
                if cluster_key not in clusters_by_key:
                    clusters_by_key[cluster_key] = {
                        "clusterName": cluster_name,
                        "site": site,
                        "segments": [],
                        "domainName": config.default_domain,  # Use configurable domain
                        "metadata": {
                            "vlan_ids": [],
                            "epg_names": [],
                            "vrfs": []
                        }
                    }

                # Add segment if not already present
                if segment_cidr not in clusters_by_key[cluster_key]["segments"]:
                    clusters_by_key[cluster_key]["segments"].append(segment_cidr)

                # Add metadata
                vlan_id = segment.get("vlan_id")
                if vlan_id and vlan_id not in clusters_by_key[cluster_key]["metadata"]["vlan_ids"]:
                    clusters_by_key[cluster_key]["metadata"]["vlan_ids"].append(vlan_id)

                epg_name = segment.get("epg_name")
                if epg_name and epg_name not in clusters_by_key[cluster_key]["metadata"]["epg_names"]:
                    clusters_by_key[cluster_key]["metadata"]["epg_names"].append(epg_name)

                vrf = segment.get("vrf")
                if vrf and vrf not in clusters_by_key[cluster_key]["metadata"]["vrfs"]:
                    clusters_by_key[cluster_key]["metadata"]["vrfs"].append(vrf)

        return list(clusters_by_key.values())

    def save_to_cache(self, data: Dict):
        """Save data to local cache file."""
        try:
            cache_data = {
                "last_updated": datetime.utcnow().isoformat(),
                "data": data
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"Cache updated successfully at {cache_data['last_updated']}")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def load_from_cache(self) -> Optional[Dict]:
        """Load data from local cache file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                logger.info(f"Loaded cache from {cache_data.get('last_updated', 'unknown time')}")
                return cache_data.get("data")
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
        return None

    async def sync_data(self) -> Dict:
        """
        Sync data from VLAN Manager API.
        Returns structured data with clusters and sites.
        """
        logger.info("Starting VLAN Manager data sync...")

        # Fetch data from API
        segments = await self.fetch_allocated_segments()
        sites = await self.fetch_sites()

        if not segments:
            logger.warning("No segments fetched, attempting to load from cache...")
            cached_data = self.load_from_cache()
            if cached_data:
                logger.info("Using cached data")
                return cached_data
            else:
                logger.error("No cached data available")
                return {"clusters": [], "sites": []}

        # Transform segments to clusters
        clusters = self.transform_to_clusters(segments)

        # Prepare data structure
        data = {
            "clusters": clusters,
            "sites": sites,
            "stats": {
                "total_clusters": len(clusters),
                "total_sites": len(sites),
                "total_segments": sum(len(c["segments"]) for c in clusters)
            }
        }

        # Save to cache
        self.save_to_cache(data)

        logger.info(f"Sync complete: {data['stats']['total_clusters']} clusters, "
                   f"{data['stats']['total_sites']} sites, "
                   f"{data['stats']['total_segments']} segments")

        return data

    async def sync_loop(self):
        """Continuous sync loop that runs every configured interval."""
        self.is_running = True
        sync_interval = config.sync_interval
        logger.info(f"VLAN sync service started (interval: {sync_interval}s, URL: {config.vlan_manager_url})")

        while self.is_running:
            try:
                await self.sync_data()
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")

            # Wait for next sync
            await asyncio.sleep(sync_interval)

    async def start(self):
        """Start the background sync service."""
        if not self.is_running:
            asyncio.create_task(self.sync_loop())

    def stop(self):
        """Stop the background sync service."""
        self.is_running = False
        logger.info("VLAN sync service stopped")


# Global instance
vlan_sync_service = VLANSyncService()
