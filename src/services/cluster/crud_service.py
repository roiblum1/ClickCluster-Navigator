"""
CRUD operations for cluster management.
Handles Create, Read, Update, Delete operations for manual clusters.
"""
from typing import List, Dict
from src.database import cluster_store
from src.utils import ClusterUtils
import logging

logger = logging.getLogger(__name__)


class ClusterCRUDService:
    """Service for CRUD operations on manual clusters."""

    def __init__(self):
        self.cluster_store = cluster_store

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
        # Prepare cluster data with LoadBalancer IP resolved BEFORE saving to cache
        # This ensures loadBalancerIP is persisted when the cluster is created
        
        # Use provided LoadBalancer IP or auto-resolve it BEFORE creating cluster
        if "loadBalancerIP" in cluster_data and cluster_data["loadBalancerIP"]:
            load_balancer_ip = cluster_data["loadBalancerIP"]
            ip_list = load_balancer_ip if isinstance(load_balancer_ip, list) else [load_balancer_ip]
            ip_count = len(ip_list)
            if ip_count == 1:
                logger.info(f"Using provided LoadBalancer IP: {ip_list[0]}")
            else:
                logger.info(f"Using provided LoadBalancer IPs ({ip_count}): {', '.join(ip_list)}")
        else:
            # Auto-resolve LoadBalancer IP before creating cluster
            load_balancer_ip = ClusterUtils.resolve_loadbalancer_ip(
                cluster_data["clusterName"],
                cluster_data.get("domainName")
            )
            if load_balancer_ip:
                ip_list = load_balancer_ip if isinstance(load_balancer_ip, list) else [load_balancer_ip]
                ip_count = len(ip_list)
                if ip_count == 1:
                    logger.info(f"Auto-resolved LoadBalancer IP: {ip_list[0]}")
                else:
                    logger.info(f"Auto-resolved LoadBalancer IPs ({ip_count}): {', '.join(ip_list)}")
            else:
                logger.debug(f"LoadBalancer IP could not be resolved for {cluster_data['clusterName']}")
        
        # Include loadBalancerIP and source in cluster_data before creating cluster
        # This ensures they are persisted when store.create_cluster() saves to cache
        cluster_data_with_metadata = cluster_data.copy()
        cluster_data_with_metadata["loadBalancerIP"] = load_balancer_ip
        cluster_data_with_metadata["source"] = "manual"
        
        # Create cluster - this will save to cache with loadBalancerIP included
        cluster = self.cluster_store.create_cluster(cluster_data_with_metadata)
        
        # Ensure source is set (in case store doesn't preserve it)
        cluster["source"] = "manual"
        # Ensure loadBalancerIP is set (in case store doesn't preserve it)
        cluster["loadBalancerIP"] = load_balancer_ip

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

