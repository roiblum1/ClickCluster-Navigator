"""
Business logic layer for cluster operations.
Handles data merging, transformation, and orchestration between data sources.
"""
from typing import List, Dict
from datetime import datetime
from src.database import cluster_store
from src.services import vlan_sync_service
from src.config import config
from src.utils import ClusterUtils
import logging

logger = logging.getLogger(__name__)


class ClusterService:
    """Service layer for cluster business logic."""

    def __init__(self):
        self.cluster_store = cluster_store
        self.vlan_service = vlan_sync_service

    def get_combined_sites(self) -> List[Dict]:
        """
        Get all sites with clusters from both VLAN Manager and manual entries.

        Business logic:
        - VLAN Manager data takes precedence for duplicate clusters
        - Manual clusters are added only if they don't exist in VLAN Manager
        - Clusters are grouped by site

        Returns:
            List of site dictionaries with clusters
        """
        # Get VLAN Manager synced data
        vlan_data = self.vlan_service.load_from_cache()

        # Get manual clusters from in-memory store
        manual_clusters = self.cluster_store.get_all_clusters()

        # Prepare combined data structure
        sites_dict = {}

        # Add VLAN Manager clusters first (they take precedence)
        if vlan_data:
            vlan_clusters = self._process_vlan_clusters(vlan_data.get("clusters", []))
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
        manual_clusters_processed = self._process_manual_clusters(
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

        # Convert to sorted list
        sites_list = list(sites_dict.values())
        sites_list.sort(key=lambda x: x["site"])

        return sites_list

    def _process_vlan_clusters(self, vlan_clusters: List[Dict]) -> List[Dict]:
        """
        Transform VLAN Manager clusters to API response format.

        Args:
            vlan_clusters: Raw clusters from VLAN Manager cache

        Returns:
            List of processed cluster dictionaries
        """
        processed = []

        for cluster in vlan_clusters:
            domain_name = cluster.get("domainName", config.default_domain)

            cluster_entry = {
                "id": f"vlan-{cluster['clusterName']}@{cluster['site']}",
                "clusterName": cluster["clusterName"],
                "site": cluster["site"],
                "segments": cluster["segments"],
                "domainName": domain_name,
                "consoleUrl": ClusterUtils.generate_console_url(
                    cluster['clusterName'],
                    domain_name
                ),
                "createdAt": datetime.utcnow().isoformat(),
                "source": "vlan-manager",
                "metadata": cluster.get("metadata", {})
            }

            processed.append(cluster_entry)

        return processed

    def _process_manual_clusters(
        self,
        manual_clusters: List[Dict],
        vlan_cluster_keys: set
    ) -> List[Dict]:
        """
        Process manual clusters, filtering out duplicates from VLAN Manager.

        Args:
            manual_clusters: Manual clusters from cluster store
            vlan_cluster_keys: Set of (clusterName, site) tuples from VLAN Manager

        Returns:
            List of manual clusters not in VLAN Manager
        """
        processed = []

        for cluster in manual_clusters:
            # Skip if this cluster already exists from VLAN Manager
            cluster_key = (cluster["clusterName"], cluster["site"])
            if cluster_key in vlan_cluster_keys:
                logger.debug(
                    f"Skipping manual cluster {cluster['clusterName']}@{cluster['site']} "
                    f"(exists in VLAN Manager)"
                )
                continue

            # Ensure source field is set
            if "source" not in cluster:
                cluster["source"] = "manual"

            processed.append(cluster)

        return processed

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

    def get_all_manual_clusters(self) -> List[Dict]:
        """
        Get all manual clusters from the cluster store.

        Returns:
            List of manual cluster dictionaries
        """
        return self.cluster_store.get_all_clusters()

    def get_cluster_by_id(self, cluster_id: str) -> Dict:
        """
        Get a specific cluster by ID.

        Args:
            cluster_id: Cluster identifier

        Returns:
            Cluster dictionary or None if not found
        """
        return self.cluster_store.get_cluster(cluster_id)

    def create_manual_cluster(self, cluster_data: Dict) -> Dict:
        """
        Create a new manual cluster.

        Args:
            cluster_data: Cluster creation data

        Returns:
            Created cluster dictionary with metadata
        """
        cluster = self.cluster_store.create_cluster(cluster_data)

        # Ensure source is set to manual
        cluster["source"] = "manual"

        logger.info(f"Created manual cluster: {cluster['clusterName']}@{cluster['site']}")

        return cluster

    def delete_manual_cluster(self, cluster_id: str) -> bool:
        """
        Delete a manual cluster.

        Args:
            cluster_id: Cluster identifier

        Returns:
            True if deletion succeeded, False otherwise
        """
        success = self.cluster_store.delete_cluster(cluster_id)

        if success:
            logger.info(f"Deleted manual cluster: {cluster_id}")
        else:
            logger.warning(f"Failed to delete cluster: {cluster_id}")

        return success

    def cluster_exists(self, cluster_name: str, site: str) -> bool:
        """
        Check if a cluster with the given name exists in a specific site.

        Args:
            cluster_name: Cluster name
            site: Site identifier

        Returns:
            True if cluster exists, False otherwise
        """
        return self.cluster_store.cluster_exists(cluster_name, site)


# Global service instance
cluster_service = ClusterService()
