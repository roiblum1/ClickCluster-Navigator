"""
Data merging logic for combining VLAN Manager and manual clusters.
Handles merging clusters from different sources with precedence rules.
"""
from typing import List, Dict
from src.services import vlan_sync_service
from src.services.cluster.processor_service import ClusterProcessorService
from src.services.cluster.ip_resolver_service import IPResolverService
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
        # Reset DNS stats at the start of processing
        IPResolverService.reset_dns_stats()
        logger.info("Starting cluster processing and DNS resolution...")

        # Get VLAN Manager synced data
        vlan_data = self.vlan_service.load_from_cache()
        logger.debug(f"Loaded VLAN data: {len(vlan_data.get('clusters', [])) if vlan_data else 0} clusters")

        # Get manual clusters from in-memory store
        from src.database import cluster_store
        manual_clusters = cluster_store.get_all_clusters()
        logger.debug(f"Loaded manual clusters: {len(manual_clusters)} clusters")

        # Prepare combined data structure
        sites_dict = {}

        # Add VLAN Manager clusters first (they take precedence)
        if vlan_data:
            vlan_clusters = self.processor.process_vlan_clusters(vlan_data.get("clusters", []))
            logger.debug(f"Processed {len(vlan_clusters)} VLAN clusters")
            for cluster in vlan_clusters:
                site_name = cluster["site"]

                if site_name not in sites_dict:
                    sites_dict[site_name] = {
                        "site": site_name,
                        "clusters": [],
                        "clusterCount": 0
                    }
                    logger.debug(f"Created new site entry: {site_name}")

                sites_dict[site_name]["clusters"].append(cluster)
                sites_dict[site_name]["clusterCount"] += 1
                logger.debug(f"Added VLAN cluster '{cluster['clusterName']}' to site '{site_name}'")

        # Add manual clusters (skip duplicates from VLAN Manager)
        vlan_cluster_keys = self._get_vlan_cluster_keys(vlan_data)
        logger.debug(f"VLAN cluster keys for deduplication: {vlan_cluster_keys}")
        manual_clusters_processed = self.processor.process_manual_clusters(
            manual_clusters,
            vlan_cluster_keys
        )
        logger.debug(f"Processed {len(manual_clusters_processed)} manual clusters (after deduplication)")

        for cluster in manual_clusters_processed:
            site_name = cluster["site"]

            if site_name not in sites_dict:
                sites_dict[site_name] = {
                    "site": site_name,
                    "clusters": [],
                    "clusterCount": 0
                }
                logger.debug(f"Created new site entry for manual cluster: {site_name}")

            sites_dict[site_name]["clusters"].append(cluster)
            sites_dict[site_name]["clusterCount"] += 1
            logger.debug(f"Added manual cluster '{cluster['clusterName']}' to site '{site_name}'")

        # Log DNS resolution statistics at INFO level after all processing
        dns_stats = IPResolverService.get_dns_stats()
        avg_time_msg = f", average time: {dns_stats['average_time_seconds']}s per request" if dns_stats['request_count'] > 0 else ""
        logger.info(
            f"Cluster processing completed - DNS resolution stats: "
            f"{dns_stats['request_count']} DNS requests, "
            f"{dns_stats['success_count']} successful, {dns_stats['failure_count']} failed, "
            f"total time: {dns_stats['total_time_seconds']}s{avg_time_msg}"
        )

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

