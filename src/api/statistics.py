"""
API routes for statistics and analytics.
"""
from fastapi import APIRouter
from typing import Dict, List
from src.database import cluster_store
from src.services import vlan_sync_service


router = APIRouter(prefix="/api/statistics", tags=["statistics"])


@router.get(
    "",
    summary="Get cluster statistics"
)
async def get_statistics() -> Dict:
    """
    Get comprehensive statistics about clusters, sites, and segments.
    """
    # Get VLAN Manager synced data
    vlan_data = vlan_sync_service.load_from_cache()
    
    # Get manual clusters
    manual_clusters = cluster_store.get_all_clusters()
    
    # Combine all clusters
    all_clusters = []
    if vlan_data:
        all_clusters.extend(vlan_data.get("clusters", []))
    all_clusters.extend(manual_clusters)
    
    # Calculate statistics
    total_clusters = len(all_clusters)
    total_sites = len(set(cluster.get("site", "unknown") for cluster in all_clusters)) if all_clusters else 0
    total_segments = sum(len(cluster.get("segments", [])) for cluster in all_clusters)
    
    # Clusters per site
    clusters_per_site = {}
    for cluster in all_clusters:
        site = cluster.get("site", "unknown")
        clusters_per_site[site] = clusters_per_site.get(site, 0) + 1
    
    # Segments per site
    segments_per_site = {}
    for cluster in all_clusters:
        site = cluster.get("site", "unknown")
        segment_count = len(cluster.get("segments", []))
        segments_per_site[site] = segments_per_site.get(site, 0) + segment_count
    
    # Domain distribution
    domain_distribution = {}
    for cluster in all_clusters:
        domain = cluster.get("domainName", "unknown")
        domain_distribution[domain] = domain_distribution.get(domain, 0) + 1
    
    # Source distribution
    source_distribution = {
        "vlan-manager": sum(1 for c in all_clusters if c.get("source") == "vlan-manager"),
        "manual": sum(1 for c in all_clusters if c.get("source") == "manual" or "source" not in c)
    }
    
    # Segments distribution (count clusters by number of segments)
    segments_count_distribution = {}
    for cluster in all_clusters:
        seg_count = len(cluster.get("segments", []))
        segments_count_distribution[seg_count] = segments_count_distribution.get(seg_count, 0) + 1
    
    return {
        "overview": {
            "total_clusters": total_clusters,
            "total_sites": total_sites,
            "total_segments": total_segments,
            "average_segments_per_cluster": round(total_segments / total_clusters, 2) if total_clusters > 0 else 0
        },
        "clusters_per_site": clusters_per_site,
        "segments_per_site": segments_per_site,
        "domain_distribution": domain_distribution,
        "source_distribution": source_distribution,
        "segments_count_distribution": segments_count_distribution
    }

