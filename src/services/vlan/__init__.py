"""
VLAN Manager integration services.

This package provides services for integrating with VLAN Manager API.
"""
from pathlib import Path
from src.services.vlan.sync_orchestrator import VLANSyncOrchestrator

# Configuration
CACHE_FILE = Path(__file__).parent.parent.parent.parent / "data" / "vlan_cache.json"

# Global orchestrator instance
vlan_sync_service = VLANSyncOrchestrator(CACHE_FILE)

__all__ = [
    "vlan_sync_service",
    "VLANSyncOrchestrator",
]
