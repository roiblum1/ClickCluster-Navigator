"""
In-memory database store for cluster management.
Can be easily replaced with SQLAlchemy/databases for production use.
"""
from typing import Dict, List, Optional
from datetime import datetime
import uuid
from collections import defaultdict
from src.utils import ClusterUtils, ClusterValidator
from src.config import config


class ClusterStore:
    """In-memory store for cluster data."""

    def __init__(self):
        self._clusters: Dict[str, dict] = {}
        self._sites: Dict[str, List[str]] = defaultdict(list)

    def create_cluster(self, cluster_data: dict) -> dict:
        """Create a new cluster entry."""
        cluster_id = str(uuid.uuid4())
        cluster_name = cluster_data["clusterName"]
        
        # Validate and normalize cluster name
        cluster_name_lower = ClusterValidator.validate_cluster_name(cluster_name)
        
        site = cluster_data["site"]
        domain_name = cluster_data.get("domainName", config.default_domain)

        # Generate console URL using utility
        console_url = ClusterUtils.generate_console_url(cluster_name_lower, domain_name)

        cluster = {
            "id": cluster_id,
            "clusterName": cluster_name_lower,
            "site": site,
            "segments": cluster_data["segments"],
            "domainName": domain_name,
            "consoleUrl": console_url,
            "createdAt": datetime.utcnow()
        }

        self._clusters[cluster_id] = cluster
        self._sites[site].append(cluster_id)

        return cluster

    def get_cluster(self, cluster_id: str) -> Optional[dict]:
        """Get cluster by ID."""
        return self._clusters.get(cluster_id)

    def get_cluster_by_name(self, cluster_name: str, site: Optional[str] = None) -> Optional[dict]:
        """Get cluster by name, optionally filtered by site."""
        for cluster in self._clusters.values():
            if cluster["clusterName"] == cluster_name:
                if site is None or cluster["site"] == site:
                    return cluster
        return None

    def get_all_clusters(self) -> List[dict]:
        """Get all clusters."""
        return list(self._clusters.values())

    def get_clusters_by_site(self, site: str) -> List[dict]:
        """Get all clusters for a specific site."""
        cluster_ids = self._sites.get(site, [])
        return [self._clusters[cid] for cid in cluster_ids if cid in self._clusters]

    def get_all_sites(self) -> Dict[str, List[dict]]:
        """Get all sites with their clusters."""
        sites_data = {}
        for site, cluster_ids in self._sites.items():
            sites_data[site] = [
                self._clusters[cid] for cid in cluster_ids if cid in self._clusters
            ]
        return sites_data

    def update_cluster(self, cluster_id: str, update_data: dict) -> Optional[dict]:
        """Update cluster information."""
        cluster = self._clusters.get(cluster_id)
        if not cluster:
            return None

        # Update site if changed
        if "site" in update_data and update_data["site"] != cluster["site"]:
            old_site = cluster["site"]
            new_site = update_data["site"]

            # Remove from old site
            if cluster_id in self._sites[old_site]:
                self._sites[old_site].remove(cluster_id)

            # Add to new site
            self._sites[new_site].append(cluster_id)

        # Update fields
        for key, value in update_data.items():
            if value is not None:
                cluster[key] = value

        # Regenerate console URL if domain changed
        if "domainName" in update_data:
            cluster["consoleUrl"] = ClusterUtils.generate_console_url(
                cluster['clusterName'],
                cluster['domainName']
            )

        return cluster

    def delete_cluster(self, cluster_id: str) -> bool:
        """Delete a cluster."""
        cluster = self._clusters.get(cluster_id)
        if not cluster:
            return False

        site = cluster["site"]
        if cluster_id in self._sites[site]:
            self._sites[site].remove(cluster_id)

        # Clean up empty sites
        if not self._sites[site]:
            del self._sites[site]

        del self._clusters[cluster_id]
        return True

    def cluster_exists(self, cluster_name: str, site: Optional[str] = None) -> bool:
        """Check if a cluster with the given name exists, optionally in a specific site."""
        for cluster in self._clusters.values():
            if cluster["clusterName"] == cluster_name:
                if site is None or cluster["site"] == site:
                    return True
        return False


# Global instance
cluster_store = ClusterStore()
