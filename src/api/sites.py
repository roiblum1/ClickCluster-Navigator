"""
API routes for site management.
"""
from fastapi import APIRouter
from typing import List
from src.models import SiteResponse
from src.database import cluster_store
from src.utils import SiteUtils

router = APIRouter(prefix="/api/sites", tags=["sites"])


@router.get(
    "",
    response_model=List[SiteResponse],
    summary="Get all sites with clusters"
)
async def get_all_sites() -> List[SiteResponse]:
    """
    Retrieve all sites organized with their clusters.
    """
    sites_data = cluster_store.get_all_sites()
    return SiteUtils.create_sites_response_list(sites_data)


@router.get(
    "/{site_name}",
    response_model=SiteResponse,
    summary="Get specific site with clusters"
)
async def get_site(site_name: str) -> SiteResponse:
    """
    Retrieve a specific site with all its clusters.
    """
    clusters = cluster_store.get_clusters_by_site(site_name)
    return SiteUtils.create_site_response(site_name, clusters)
