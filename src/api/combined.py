"""
Combined API endpoint that merges VLAN Manager data with manual clusters.
"""
from fastapi import APIRouter
from typing import List
from datetime import datetime
from src.database import cluster_store
from src.services import vlan_sync_service
from src.models import SiteResponse
from src.config import config

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
    """
    # Get VLAN Manager synced data
    vlan_data = vlan_sync_service.load_from_cache()

    # Get manual clusters from in-memory store
    manual_clusters = cluster_store.get_all_clusters()

    # Prepare combined data structure
    sites_dict = {}

    # Add VLAN Manager clusters first
    if vlan_data:
        for cluster in vlan_data.get("clusters", []):
            site_name = cluster["site"]

            if site_name not in sites_dict:
                sites_dict[site_name] = {
                    "site": site_name,
                    "clusters": [],
                    "clusterCount": 0
                }

            # Transform to match ClusterResponse format
            # Use composite key for unique ID to support duplicate names across sites
            domain_name = cluster.get("domainName", config.default_domain)
            cluster_entry = {
                "id": f"vlan-{cluster['clusterName']}@{cluster['site']}",
                "clusterName": cluster["clusterName"],
                "site": cluster["site"],
                "segments": cluster["segments"],
                "domainName": domain_name,
                "consoleUrl": f"https://console-openshift-console.{cluster['clusterName']}.apps.{domain_name}",
                "createdAt": datetime.utcnow().isoformat(),  # Use current time for VLAN Manager clusters
                "source": "vlan-manager",
                "metadata": cluster.get("metadata", {})
            }

            sites_dict[site_name]["clusters"].append(cluster_entry)
            sites_dict[site_name]["clusterCount"] += 1

    # Add manual clusters (skip if already exists from VLAN Manager)
    # Use composite key (clusterName, site) to properly identify duplicates
    vlan_cluster_keys = set()
    if vlan_data:
        vlan_cluster_keys = {(c["clusterName"], c["site"]) for c in vlan_data.get("clusters", [])}

    for cluster in manual_clusters:
        # Skip if this cluster already exists from VLAN Manager (same name AND site)
        cluster_key = (cluster["clusterName"], cluster["site"])
        if cluster_key in vlan_cluster_keys:
            continue

        site_name = cluster["site"]

        if site_name not in sites_dict:
            sites_dict[site_name] = {
                "site": site_name,
                "clusters": [],
                "clusterCount": 0
            }

        # Add source indicator
        cluster["source"] = "manual"

        sites_dict[site_name]["clusters"].append(cluster)
        sites_dict[site_name]["clusterCount"] += 1

    # Convert to list and sort
    sites_list = list(sites_dict.values())
    sites_list.sort(key=lambda x: x["site"])

    return sites_list
