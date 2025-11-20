"""
API routes for VLAN Manager sync data.
"""
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from typing import Dict
from src.services import vlan_sync_service
from src.config import config

router = APIRouter(prefix="/api/vlan-sync", tags=["vlan-sync"])


@router.get(
    "/data",
    summary="Get synced VLAN Manager data"
)
async def get_synced_data() -> Dict:
    """
    Get the latest synced data from VLAN Manager.
    Returns clusters, sites, and statistics.
    Falls back to cached data if API is unavailable.
    """
    # Try to load from cache first (fastest)
    cached_data = vlan_sync_service.load_from_cache()

    if cached_data:
        return cached_data
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VLAN Manager data not available and no cache exists"
        )


@router.post(
    "/sync",
    summary="Trigger manual sync"
)
async def trigger_sync() -> Dict:
    """
    Manually trigger a sync with VLAN Manager API.
    Useful for immediate updates without waiting for the scheduled sync.
    """
    try:
        data = await vlan_sync_service.sync_data()
        return {
            "status": "success",
            "message": "Sync completed successfully",
            "data": data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.get(
    "/status",
    summary="Get sync service status"
)
async def get_sync_status() -> Dict:
    """Get the current status of the VLAN sync service."""
    cache_exists = vlan_sync_service.cache_file.exists()
    cache_age = None
    last_updated = None

    if cache_exists:
        cache_mtime = os.path.getmtime(vlan_sync_service.cache_file)
        cache_age = (datetime.now().timestamp() - cache_mtime) / 60  # in minutes
        last_updated = datetime.fromtimestamp(cache_mtime).isoformat()

    return {
        "service_running": vlan_sync_service.is_running,
        "sync_interval_seconds": config.sync_interval,
        "cache_exists": cache_exists,
        "cache_age_minutes": round(cache_age, 2) if cache_age else None,
        "last_updated": last_updated,
        "vlan_manager_url": config.vlan_manager_url
    }
