"""
VLAN Manager API client service.
Handles HTTP communication with VLAN Manager API.
"""
import httpx
from typing import List, Dict, Optional
import logging
import warnings
from src.config import config

# Suppress SSL warnings when verify=False
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

logger = logging.getLogger(__name__)


class VLANApiClient:
    """Client for communicating with VLAN Manager API."""

    def __init__(self, timeout: float = 10.0):
        """
        Initialize VLAN API client.

        Args:
            timeout: HTTP request timeout in seconds
        """
        self._timeout = timeout

    async def fetch_from_api(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
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
            full_url = f"{vlan_url}{endpoint}"

            # Check if insecure TLS verification is enabled (verify=False)
            insecure_tls = config.vlan_manager_insecure_tls_verify
            verify = not insecure_tls  # If insecure_tls=True, then verify=False

            logger.debug(f"Attempting to fetch from: {full_url} (verify={verify})")

            async with httpx.AsyncClient(timeout=self._timeout, verify=verify) as client:
                response = await client.get(full_url, params=params)
                response.raise_for_status()
                logger.debug(f"Successfully fetched from {endpoint}")
                return response.json()

        except httpx.ConnectError as e:
            logger.error(f"Connection error to {endpoint}: {e}. "
                        f"Check if VLAN Manager is running at {config.vlan_manager_url}")
            return None
        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching from {endpoint}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch from {endpoint}: {type(e).__name__}: {e}")
            return None

    async def fetch_allocated_segments(self) -> List[Dict]:
        """
        Fetch only allocated segments from VLAN Manager API.

        Returns:
            List of allocated segment dictionaries
        """
        data = await self.fetch_from_api("/api/segments", params={"allocated": True})
        return data if data is not None else []

    async def fetch_sites(self) -> List[str]:
        """
        Fetch available sites from VLAN Manager API.

        Returns:
            List of site names
        """
        data = await self.fetch_from_api("/api/sites")
        return data.get("sites", []) if data else []
