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
from src.utils import ClusterValidator

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
        self._http_timeout = 10.0

    async def _fetch_from_api(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Generic method to fetch data from VLAN Manager API.
        
        Args:
            endpoint: API endpoint path (e.g., '/api/segments')
            params: Optional query parameters
            
        Returns:
            JSON response data or None on error
        """
        try:
            vlan_url = config.vlan_manager_url
            async with httpx.AsyncClient(timeout=self._http_timeout) as client:
                response = await client.get(f"{vlan_url}{endpoint}", params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch from {endpoint}: {e}")
            return None

    async def fetch_allocated_segments(self) -> List[Dict]:
        """Fetch only allocated segments from VLAN Manager API."""
        data = await self._fetch_from_api("/api/segments", params={"allocated": True})
        return data if data is not None else []

    async def fetch_sites(self) -> List[str]:
        """Fetch available sites from VLAN Manager API."""
        data = await self._fetch_from_api("/api/sites")
        return data.get("sites", []) if data else []

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

                # Only process clusters that start with 'ocp4-'
                if not ClusterValidator.is_valid_cluster_name(cluster_name):
                    logger.debug(f"Skipping cluster '{cluster_name}' - does not start with 'ocp4-'")
                    continue

                # Normalize and use composite key (cluster_name, site) to allow duplicate names across sites
                cluster_name_lower = ClusterValidator.validate_cluster_name(cluster_name)
                cluster_key = f"{cluster_name_lower}@{site}"

                # Initialize cluster entry if not exists
                if cluster_key not in clusters_by_key:
                    clusters_by_key[cluster_key] = {
                        "clusterName": cluster_name_lower,
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

                # Add metadata using helper method
                VLANSyncService._add_to_metadata_list(
                    clusters_by_key[cluster_key]["metadata"],
                    "vlan_ids",
                    segment.get("vlan_id")
                )
                VLANSyncService._add_to_metadata_list(
                    clusters_by_key[cluster_key]["metadata"],
                    "epg_names",
                    segment.get("epg_name")
                )
                VLANSyncService._add_to_metadata_list(
                    clusters_by_key[cluster_key]["metadata"],
                    "vrfs",
                    segment.get("vrf")
                )

        return list(clusters_by_key.values())

    @staticmethod
    def _add_to_metadata_list(metadata: Dict, key: str, value: Optional[str]) -> None:
        """
        Add value to metadata list if it exists and is not already present.
        
        Args:
            metadata: Metadata dictionary
            key: Key in metadata dictionary (list key)
            value: Value to add (if not None)
        """
        if value and value not in metadata.get(key, []):
            if key not in metadata:
                metadata[key] = []
            metadata[key].append(value)

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
