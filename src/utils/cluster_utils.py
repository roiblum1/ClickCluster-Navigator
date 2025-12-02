"""
Cluster utilities - Backward compatibility wrapper.

DEPRECATED: This module is kept for backward compatibility.
Use the following instead:
- src.utils.validators.ClusterValidator for validation
- src.services.cluster.IPResolverService for IP resolution
- src.services.cluster.URLGeneratorService for URL generation
"""
from src.utils.validators import ClusterValidator
from src.services.cluster import IPResolverService, URLGeneratorService


class ClusterUtils:
    """
    Utility class for cluster operations.

    DEPRECATED: Use specific services instead.
    """

    @staticmethod
    def generate_console_url(cluster_name: str, domain_name: str = None) -> str:
        """Generate OpenShift console URL. Use URLGeneratorService instead."""
        return URLGeneratorService.generate_console_url(cluster_name, domain_name)

    @staticmethod
    def normalize_cluster_name(cluster_name: str) -> str:
        """Normalize cluster name. Use ClusterValidator.normalize_cluster_name instead."""
        return ClusterValidator.normalize_cluster_name(cluster_name)

    @staticmethod
    def resolve_loadbalancer_ip(cluster_name: str, domain_name: str = None) -> str:
        """Resolve LoadBalancer IP. Use IPResolverService instead."""
        return IPResolverService.resolve_loadbalancer_ip(cluster_name, domain_name)


__all__ = ["ClusterUtils", "ClusterValidator"]
