"""
API routes for cluster management (Read-only - data fetched from VLAN Manager).
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from src.models import ClusterResponse, ClusterCreate
from src.services.cluster import cluster_service
from src.auth import get_current_admin
from src.exceptions import (
    ClusterNotFoundError,
    ClusterAlreadyExistsError,
    VLANManagerClusterProtectedError
)

router = APIRouter(prefix="/api/clusters", tags=["clusters"])


@router.get(
    "",
    response_model=List[ClusterResponse],
    summary="Get all clusters"
)
async def get_all_clusters() -> List[ClusterResponse]:
    """
    Get all manual clusters.
    Note: Primary data source is VLAN Manager. Use /api/sites-combined for complete data.
    """
    clusters = cluster_service.get_all_manual_clusters()
    return [ClusterResponse(**cluster) for cluster in clusters]


@router.get(
    "/{cluster_id}",
    response_model=ClusterResponse,
    summary="Get a specific cluster by ID"
)
async def get_cluster(cluster_id: str) -> ClusterResponse:
    """Get details of a specific cluster by its ID."""
    try:
        cluster = cluster_service.get_cluster_by_id(cluster_id)

        if not cluster:
            raise ClusterNotFoundError(cluster_id)

        return ClusterResponse(**cluster)

    except ClusterNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )


@router.post(
    "",
    response_model=ClusterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new cluster (Admin only)",
    dependencies=[Depends(get_current_admin)]
)
async def create_cluster(cluster_data: ClusterCreate) -> ClusterResponse:
    """
    Create a new manual cluster entry.
    Requires admin authentication.

    - **clusterName**: Must start with 'ocp4-', lowercase alphanumeric with hyphens
    - **site**: Site identifier
    - **segments**: List of network segments in CIDR notation
    - **domainName**: Optional domain name (defaults to config value)
    """
    try:
        # Check if cluster already exists (same name and site)
        if cluster_service.cluster_exists(cluster_data.clusterName, cluster_data.site):
            raise ClusterAlreadyExistsError(cluster_data.clusterName, cluster_data.site)

        # Create cluster using service layer
        cluster_dict = {
            "clusterName": cluster_data.clusterName,
            "site": cluster_data.site,
            "segments": cluster_data.segments,
            "domainName": cluster_data.domainName or "example.com",
            "loadBalancerIP": cluster_data.loadBalancerIP
        }

        cluster = cluster_service.create_manual_cluster(cluster_dict)

        return ClusterResponse(**cluster)

    except ClusterAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )


@router.post(
    "/bulk",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create multiple clusters (Admin only - CSV/Bulk)",
    dependencies=[Depends(get_current_admin)]
)
async def create_clusters_bulk(clusters_data: List[ClusterCreate]):
    """
    Create multiple clusters in a single request (bulk operation).
    Requires admin authentication.

    Accepts a list of cluster objects. Each cluster must have:
    - **clusterName**: Must start with 'ocp4-', lowercase alphanumeric with hyphens
    - **site**: Site identifier
    - **segments**: List of network segments in CIDR notation
    - **domainName**: Optional domain name (defaults to config value)
    - **loadBalancerIP**: Optional LoadBalancer IP (will be auto-resolved if not provided)

    Returns summary of created clusters and any errors encountered.
    """
    results = {
        "success": [],
        "failed": [],
        "total": len(clusters_data),
        "created_count": 0,
        "failed_count": 0
    }

    for cluster_data in clusters_data:
        try:
            # Check if cluster already exists
            if cluster_service.cluster_exists(cluster_data.clusterName, cluster_data.site):
                results["failed"].append({
                    "clusterName": cluster_data.clusterName,
                    "site": cluster_data.site,
                    "error": f"Cluster already exists"
                })
                results["failed_count"] += 1
                continue

            # Create cluster
            cluster_dict = {
                "clusterName": cluster_data.clusterName,
                "site": cluster_data.site,
                "segments": cluster_data.segments,
                "domainName": cluster_data.domainName or "example.com",
                "loadBalancerIP": cluster_data.loadBalancerIP
            }

            cluster = cluster_service.create_manual_cluster(cluster_dict)

            results["success"].append({
                "id": cluster["id"],
                "clusterName": cluster["clusterName"],
                "site": cluster["site"],
                "loadBalancerIP": cluster.get("loadBalancerIP")
            })
            results["created_count"] += 1

        except Exception as e:
            results["failed"].append({
                "clusterName": cluster_data.clusterName,
                "site": cluster_data.site,
                "error": str(e)
            })
            results["failed_count"] += 1

    return results


@router.delete(
    "/{cluster_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a cluster (Admin only)",
    dependencies=[Depends(get_current_admin)]
)
async def delete_cluster(cluster_id: str):
    """
    Delete a manual cluster entry.
    Requires admin authentication.
    Only manual clusters can be deleted (not VLAN Manager clusters).
    """
    try:
        # Get the cluster first to check if it exists
        cluster = cluster_service.get_cluster_by_id(cluster_id)

        if not cluster:
            raise ClusterNotFoundError(cluster_id)

        # Check if it's a manual cluster (VLAN Manager clusters cannot be deleted)
        if cluster.get("source") == "vlan-manager":
            raise VLANManagerClusterProtectedError(cluster_id)

        # Delete the cluster
        success = cluster_service.delete_manual_cluster(cluster_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete cluster"
            )

        return None

    except ClusterNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except VLANManagerClusterProtectedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message
        )
