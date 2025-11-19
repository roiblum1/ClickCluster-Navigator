"""
Utility functions for cluster operations.
"""
from typing import Optional
from src.config import config


class ClusterValidator:
    """Utility class for cluster validation."""

    CLUSTER_PREFIX = "ocp4-"

    @staticmethod
    def validate_cluster_name(cluster_name: str) -> str:
        """
        Validate and normalize cluster name.
        
        Args:
            cluster_name: The cluster name to validate
            
        Returns:
            Normalized cluster name (lowercase, stripped)
            
        Raises:
            ValueError: If cluster name doesn't start with 'ocp4-'
        """
        cluster_name_lower = cluster_name.lower().strip()
        
        if not cluster_name_lower.startswith(ClusterValidator.CLUSTER_PREFIX):
            raise ValueError(
                f"Cluster name '{cluster_name}' must start with '{ClusterValidator.CLUSTER_PREFIX}' prefix"
            )
        
        return cluster_name_lower

    @staticmethod
    def is_valid_cluster_name(cluster_name: str) -> bool:
        """
        Check if cluster name is valid (starts with 'ocp4-').
        
        Args:
            cluster_name: The cluster name to check
            
        Returns:
            True if valid, False otherwise
        """
        try:
            ClusterValidator.validate_cluster_name(cluster_name)
            return True
        except ValueError:
            return False


class ClusterUtils:
    """Utility class for cluster operations."""

    @staticmethod
    def generate_console_url(cluster_name: str, domain_name: Optional[str] = None) -> str:
        """
        Generate OpenShift console URL for a cluster.
        
        Args:
            cluster_name: The cluster name
            domain_name: Optional domain name (defaults to config value)
            
        Returns:
            Console URL string
        """
        if domain_name is None:
            domain_name = config.default_domain
        
        cluster_name_lower = cluster_name.lower().strip()
        return f"https://console-openshift-console.{cluster_name_lower}.apps.{domain_name}"

    @staticmethod
    def normalize_cluster_name(cluster_name: str) -> str:
        """
        Normalize cluster name to lowercase and strip whitespace.
        
        Args:
            cluster_name: The cluster name to normalize
            
        Returns:
            Normalized cluster name
        """
        return cluster_name.lower().strip()

