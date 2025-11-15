"""
API routes for site management.
"""
from fastapi import APIRouter
from typing import List, Dict
from src.models import SiteResponse, ClusterResponse
from src.database import cluster_store

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

    sites_response = []
    for site_name, clusters in sites_data.items():
        site_response = SiteResponse(
            site=site_name,
            clusterCount=len(clusters),
            clusters=[ClusterResponse(**cluster) for cluster in clusters]
        )
        sites_response.append(site_response)

    # Sort by site name
    sites_response.sort(key=lambda x: x.site)

    return sites_response


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

    return SiteResponse(
        site=site_name,
        clusterCount=len(clusters),
        clusters=[ClusterResponse(**cluster) for cluster in clusters]
    )
