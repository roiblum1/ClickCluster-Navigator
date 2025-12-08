"""
API routes package initialization.
"""
from .clusters import router as clusters_router
from .sites import router as sites_router
from .vlan_sync import router as vlan_sync_router
from .combined import router as combined_router
from .statistics import router as statistics_router
from .export import router as export_router
from .dns import router as dns_router

__all__ = ["clusters_router", "sites_router", "vlan_sync_router", "combined_router", "statistics_router", "export_router", "dns_router"]
