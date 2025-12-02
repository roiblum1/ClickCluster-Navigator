"""
Cluster name validation service.
Validates cluster names according to naming conventions.
"""
import logging

logger = logging.getLogger(__name__)


class ClusterValidator:
    """Validator for cluster naming conventions."""

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
                f"Cluster name '{cluster_name}' must start with "
                f"'{ClusterValidator.CLUSTER_PREFIX}' prefix"
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
