"""
VLAN data transformation service.
Handles transformation of VLAN segments to cluster data structure.
"""
from typing import List, Dict, Optional
import logging
from src.config import config
from src.utils.validators import ClusterValidator

logger = logging.getLogger(__name__)


class VLANDataTransformer:
    """Service for transforming VLAN Manager data to cluster structures."""

    @staticmethod
    def transform_segments_to_clusters(segments: List[Dict]) -> List[Dict]:
        """
        Transform VLAN segments to cluster data structure.

        Groups segments by cluster_name and site.
        Uses composite key (cluster_name, site) to allow duplicate cluster names across different sites.
        Handles comma-separated cluster names (when multiple clusters share a segment).

        Args:
            segments: List of segment dictionaries from VLAN Manager

        Returns:
            List of cluster dictionaries
        """
        clusters_by_key = {}

        for segment in segments:
            cluster_name_raw = segment.get("cluster_name")
            site = segment.get("site")
            segment_cidr = segment.get("segment")

            # Skip segments without cluster allocation
            if not cluster_name_raw or not site or not segment_cidr:
                continue

            # Skip released segments
            if segment.get("released", False):
                continue

            # Handle comma-separated cluster names (e.g., "ocp4-roi,ocp4-roi2")
            cluster_names = [name.strip() for name in cluster_name_raw.split(",")]

            for cluster_name in cluster_names:
                # Skip empty names
                if not cluster_name:
                    continue

                # Only process clusters that start with 'ocp4-'
                if not ClusterValidator.is_valid_cluster_name(cluster_name):
                    logger.debug(f"Skipping cluster '{cluster_name}' - does not start with 'ocp4-'")
                    continue

                # Normalize and use composite key (cluster_name, site)
                cluster_name_lower = ClusterValidator.validate_cluster_name(cluster_name)
                cluster_key = f"{cluster_name_lower}@{site}"

                # Initialize cluster entry if not exists
                if cluster_key not in clusters_by_key:
                    clusters_by_key[cluster_key] = {
                        "clusterName": cluster_name_lower,
                        "site": site,
                        "segments": [],
                        "domainName": config.default_domain,
                        "source": "vlan-manager",
                        "metadata": {
                            "vlan_ids": [],
                            "epg_names": [],
                            "vrfs": []
                        }
                    }

                # Add segment if not already present
                if segment_cidr not in clusters_by_key[cluster_key]["segments"]:
                    clusters_by_key[cluster_key]["segments"].append(segment_cidr)

                # Add metadata
                VLANDataTransformer._add_to_metadata_list(
                    clusters_by_key[cluster_key]["metadata"],
                    "vlan_ids",
                    segment.get("vlan_id")
                )
                VLANDataTransformer._add_to_metadata_list(
                    clusters_by_key[cluster_key]["metadata"],
                    "epg_names",
                    segment.get("epg_name")
                )
                VLANDataTransformer._add_to_metadata_list(
                    clusters_by_key[cluster_key]["metadata"],
                    "vrfs",
                    segment.get("vrf")
                )

        return list(clusters_by_key.values())

    @staticmethod
    def _add_to_metadata_list(metadata: Dict, key: str, value: Optional[str]) -> None:
        """
        Add value to metadata list if it exists and is not already present.

        Args:
            metadata: Metadata dictionary
            key: Key in metadata dictionary (list key)
            value: Value to add (if not None)
        """
        if value and value not in metadata.get(key, []):
            if key not in metadata:
                metadata[key] = []
            metadata[key].append(value)

    @staticmethod
    def calculate_stats(clusters: List[Dict], sites: List[str]) -> Dict:
        """
        Calculate statistics from cluster data.

        Args:
            clusters: List of cluster dictionaries
            sites: List of site names

        Returns:
            Dictionary with statistics
        """
        return {
            "total_clusters": len(clusters),
            "total_sites": len(sites),
            "total_segments": sum(len(c["segments"]) for c in clusters)
        }
