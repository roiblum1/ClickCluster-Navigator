"""
API routes for VLAN Manager sync data.
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict
from src.services import vlan_sync_service
from src.services.vlan_sync_status_service import vlan_sync_status_service

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
    return vlan_sync_status_service.get_sync_status()


@router.get(
    "/sites",
    summary="Get available sites from VLAN Manager"
)
async def get_sites() -> Dict:
    """
    Get the list of available sites from VLAN Manager.
    Returns a list of unique site names.
    """
    return vlan_sync_status_service.get_sites()
