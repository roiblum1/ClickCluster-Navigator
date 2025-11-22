"""
Combined API endpoint that merges VLAN Manager data with manual clusters.
"""
from fastapi import APIRouter
from typing import List
from src.models import SiteResponse
from src.services.cluster_service import cluster_service

router = APIRouter(prefix="/api", tags=["combined"])


@router.get(
    "/sites-combined",
    response_model=List[SiteResponse],
    summary="Get all sites with combined data from VLAN Manager and manual entries"
)
async def get_combined_sites() -> List[SiteResponse]:
    """
    Get sites with clusters from both VLAN Manager (synced) and manual entries.
    VLAN Manager data takes precedence for clusters that exist in both sources.

    Business logic is handled by ClusterService layer.
    """
    return cluster_service.get_combined_sites()
