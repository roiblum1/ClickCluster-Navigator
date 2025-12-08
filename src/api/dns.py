"""
DNS statistics API endpoints.
"""
from fastapi import APIRouter
from src.services.cluster import IPResolverService

router = APIRouter(prefix="/api/dns", tags=["DNS"])


@router.get("/stats")
async def get_dns_stats():
    """
    Get DNS resolution statistics.

    Returns statistics about DNS resolution requests including:
    - Total request count
    - Success/failure counts
    - Total and average resolution time
    """
    return IPResolverService.get_dns_stats()


@router.post("/stats/reset")
async def reset_dns_stats():
    """Reset DNS resolution statistics."""
    IPResolverService.reset_dns_stats()
    return {
        "status": "success",
        "message": "DNS statistics reset"
    }
