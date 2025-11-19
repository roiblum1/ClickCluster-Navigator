"""
Utility functions for site operations.
"""
from typing import List, Dict
from src.models import SiteResponse, ClusterResponse


class SiteUtils:
    """Utility class for site operations."""

    @staticmethod
    def create_site_response(site_name: str, clusters: List[Dict]) -> SiteResponse:
        """
        Create a SiteResponse from site name and cluster dictionaries.
        
        Args:
            site_name: The site name
            clusters: List of cluster dictionaries
            
        Returns:
            SiteResponse object
        """
        return SiteResponse(
            site=site_name,
            clusterCount=len(clusters),
            clusters=[ClusterResponse(**cluster) for cluster in clusters]
        )

    @staticmethod
    def create_sites_response_list(sites_data: Dict[str, List[Dict]]) -> List[SiteResponse]:
        """
        Create a list of SiteResponse objects from sites dictionary.
        
        Args:
            sites_data: Dictionary mapping site names to cluster lists
            
        Returns:
            Sorted list of SiteResponse objects
        """
        sites_response = [
            SiteUtils.create_site_response(site_name, clusters)
            for site_name, clusters in sites_data.items()
        ]
        sites_response.sort(key=lambda x: x.site)
        return sites_response

