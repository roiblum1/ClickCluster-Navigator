"""
Cluster URL generation service.
Generates URLs for cluster resources (console, API, etc.).
"""
from typing import Optional
from src.config import config


class URLGeneratorService:
    """Service for generating cluster-related URLs."""

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
        return f"https://console-openshift-console.apps.{cluster_name_lower}.{domain_name}"
