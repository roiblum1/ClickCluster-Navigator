"""
API routes for statistics and analytics.
"""
from fastapi import APIRouter
from typing import Dict
from src.services.statistics_service import statistics_service


router = APIRouter(prefix="/api/statistics", tags=["statistics"])


@router.get(
    "",
    summary="Get cluster statistics"
)
async def get_statistics() -> Dict:
    """
    Get comprehensive statistics about clusters, sites, and segments.
    """
    return statistics_service.get_statistics()

