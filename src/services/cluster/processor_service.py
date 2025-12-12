"""
Cluster processing and transformation logic.
Handles processing of VLAN Manager clusters and manual clusters.
"""
from typing import List, Dict
from datetime import datetime
from src.config import config
from src.utils import ClusterUtils
import logging

logger = logging.getLogger(__name__)


class ClusterProcessorService:
    """Service for processing and transforming cluster data."""

    def process_vlan_clusters(self, vlan_clusters: List[Dict]) -> List[Dict]:
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

            # Resolve LoadBalancer IP (always returns list or None)
            load_balancer_ip = ClusterUtils.resolve_loadbalancer_ip(
                cluster['clusterName'],
                domain_name
            )

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
                "loadBalancerIP": load_balancer_ip,  # Already a list or None
                "metadata": cluster.get("metadata", {})
            }

            processed.append(cluster_entry)

        return processed

    def process_manual_clusters(
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

            # Normalize LoadBalancer IP to list format (handle backward compatibility)
            if "loadBalancerIP" in cluster and cluster["loadBalancerIP"] is not None:
                # Normalize: convert string to list, keep list as-is
                if isinstance(cluster["loadBalancerIP"], str):
                    cluster["loadBalancerIP"] = [cluster["loadBalancerIP"]]
                elif not isinstance(cluster["loadBalancerIP"], list):
                    # Invalid type, reset to None so it gets resolved
                    cluster["loadBalancerIP"] = None
            else:
                # Resolve LoadBalancer IP if not already present
                cluster["loadBalancerIP"] = ClusterUtils.resolve_loadbalancer_ip(
                    cluster["clusterName"],
                    cluster.get("domainName")
                )

            processed.append(cluster)

        return processed

