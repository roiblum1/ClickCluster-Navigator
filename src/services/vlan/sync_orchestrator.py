"""
VLAN sync orchestrator service.
Orchestrates the synchronization process between VLAN Manager API and local cache.
"""
import asyncio
from typing import Dict
import logging
from pathlib import Path
from src.config import config
from src.services.vlan.api_client import VLANApiClient
from src.services.vlan.data_transformer import VLANDataTransformer
from src.services.vlan.cache_service import VLANCacheService

logger = logging.getLogger(__name__)


class VLANSyncOrchestrator:
    """
    Orchestrates VLAN Manager synchronization.

    Coordinates API client, data transformer, and cache service
    to sync VLAN Manager data with local storage.
    """

    def __init__(self, cache_file: Path):
        """
        Initialize sync orchestrator.

        Args:
            cache_file: Path to cache file
        """
        self.cache_file = cache_file
        self.api_client = VLANApiClient()
        self.transformer = VLANDataTransformer()
        self.cache_service = VLANCacheService(cache_file)
        self.is_running = False

    async def sync_data(self) -> Dict:
        """
        Sync data from VLAN Manager API.

        Returns:
            Structured data with clusters and sites
        """
        logger.info("Starting VLAN Manager data sync...")

        # Fetch data from API
        segments = await self.api_client.fetch_allocated_segments()
        sites = await self.api_client.fetch_sites()

        # Fall back to cache if API fails
        if not segments:
            logger.warning("No segments fetched, attempting to load from cache...")
            cached_data = self.cache_service.load()
            if cached_data:
                logger.info("Using cached data")
                return cached_data
            else:
                logger.error("No cached data available")
                return {"clusters": [], "sites": []}

        # Transform segments to clusters
        clusters = self.transformer.transform_segments_to_clusters(segments)

        # Calculate statistics
        stats = self.transformer.calculate_stats(clusters, sites)

        # Prepare data structure
        data = {
            "clusters": clusters,
            "sites": sites,
            "stats": stats
        }

        # Save to cache
        self.cache_service.save(data)

        logger.info(f"Sync complete: {stats['total_clusters']} clusters, "
                   f"{stats['total_sites']} sites, "
                   f"{stats['total_segments']} segments")

        return data

    async def sync_loop(self):
        """Continuous sync loop that runs every configured interval."""
        self.is_running = True
        sync_interval = config.sync_interval
        logger.info(f"VLAN sync service started (interval: {sync_interval}s, "
                   f"URL: {config.vlan_manager_url})")

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

    def load_from_cache(self) -> Dict:
        """
        Load data from cache.

        Returns:
            Cached data or empty structure
        """
        data = self.cache_service.load()
        return data if data else {"clusters": [], "sites": []}
