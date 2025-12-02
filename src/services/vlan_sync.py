"""
Background service to sync data from VLAN Manager API.

DEPRECATED: This module is kept for backward compatibility.
Use src.services.vlan.sync_orchestrator instead.
"""
from src.services.vlan import vlan_sync_service

# Re-export for backward compatibility
VLANSyncService = type(vlan_sync_service)

__all__ = ["vlan_sync_service", "VLANSyncService"]
