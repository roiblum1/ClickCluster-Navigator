"""
API routes for cluster management (Read-only - data fetched from VLAN Manager).
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from src.models import ClusterResponse
from src.database import cluster_store

router = APIRouter(prefix="/api/clusters", tags=["clusters"])


@router.get(
    "",
    response_model=List[ClusterResponse],
    summary="Get all clusters"
)
async def get_all_clusters() -> List[ClusterResponse]:
    """
    Get all clusters.
    Note: Primary data source is VLAN Manager. Use /api/sites-combined for complete data.
    """
    clusters = cluster_store.get_all_clusters()
    return [ClusterResponse(**cluster) for cluster in clusters]


@router.get(
    "/{cluster_id}",
    response_model=ClusterResponse,
    summary="Get a specific cluster by ID"
)
async def get_cluster(cluster_id: str) -> ClusterResponse:
    """Get details of a specific cluster by its ID."""
    cluster = cluster_store.get_cluster(cluster_id)

    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster with ID '{cluster_id}' not found"
        )

    return ClusterResponse(**cluster)
