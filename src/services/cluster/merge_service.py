"""
Data merging logic for combining VLAN Manager and manual clusters.
Handles merging clusters from different sources with precedence rules.
"""
from typing import List, Dict
from src.services import vlan_sync_service
from src.services.cluster.processor_service import ClusterProcessorService
from src.utils import SiteUtils
import logging

logger = logging.getLogger(__name__)


class ClusterMergeService:
    """Service for merging cluster data from multiple sources."""

    def __init__(self):
        self.vlan_service = vlan_sync_service
        self.processor = ClusterProcessorService()

    def get_combined_sites(self):
        """
        Get all sites with clusters from both VLAN Manager and manual entries.

        Business logic:
        - VLAN Manager data takes precedence for duplicate clusters
        - Manual clusters are added only if they don't exist in VLAN Manager
        - Clusters are grouped by site

        Returns:
            List of SiteResponse objects with clusters
        """
        # Get VLAN Manager synced data
        vlan_data = self.vlan_service.load_from_cache()

        # Get manual clusters from in-memory store
        from src.database import cluster_store
        manual_clusters = cluster_store.get_all_clusters()

        # Prepare combined data structure
        sites_dict = {}

        # Add VLAN Manager clusters first (they take precedence)
        if vlan_data:
            vlan_clusters = self.processor.process_vlan_clusters(vlan_data.get("clusters", []))
            for cluster in vlan_clusters:
                site_name = cluster["site"]

                if site_name not in sites_dict:
                    sites_dict[site_name] = {
                        "site": site_name,
                        "clusters": [],
                        "clusterCount": 0
                    }

                sites_dict[site_name]["clusters"].append(cluster)
                sites_dict[site_name]["clusterCount"] += 1

        # Add manual clusters (skip duplicates from VLAN Manager)
        vlan_cluster_keys = self._get_vlan_cluster_keys(vlan_data)
        manual_clusters_processed = self.processor.process_manual_clusters(
            manual_clusters,
            vlan_cluster_keys
        )

        for cluster in manual_clusters_processed:
            site_name = cluster["site"]

            if site_name not in sites_dict:
                sites_dict[site_name] = {
                    "site": site_name,
                    "clusters": [],
                    "clusterCount": 0
                }

            sites_dict[site_name]["clusters"].append(cluster)
            sites_dict[site_name]["clusterCount"] += 1

        # Convert to SiteResponse objects
        sites_response = [
            SiteUtils.create_site_response(site_data["site"], site_data["clusters"])
            for site_data in sites_dict.values()
        ]
        sites_response.sort(key=lambda x: x.site)

        return sites_response

    def _get_vlan_cluster_keys(self, vlan_data: Dict) -> set:
        """
        Extract unique cluster keys from VLAN Manager data.

        Args:
            vlan_data: VLAN Manager cache data

        Returns:
            Set of (clusterName, site) tuples
        """
        if not vlan_data:
            return set()

        clusters = vlan_data.get("clusters", [])
        return {(c["clusterName"], c["site"]) for c in clusters}

