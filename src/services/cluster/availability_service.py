"""
Cluster availability checking via HTTP HEAD requests to console URLs.
"""
import asyncio
import logging
from typing import Dict, List

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 5.0


class AvailabilityService:

    async def _check_one(self, cluster_id: str, console_url: str) -> tuple:
        try:
            async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=_TIMEOUT) as client:
                await client.head(console_url)
            return cluster_id, True
        except Exception:
            return cluster_id, False

    async def check_all(self, clusters: List[Dict]) -> Dict[str, bool]:
        """Check availability for all clusters concurrently. Any HTTP response = available."""
        tasks = [
            self._check_one(c["id"], c["consoleUrl"])
            for c in clusters
            if c.get("consoleUrl")
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            cluster_id: available
            for result in results
            if isinstance(result, tuple)
            for cluster_id, available in [result]
        }


availability_service = AvailabilityService()
