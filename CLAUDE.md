# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Local development (creates venv, installs deps, runs on :8000)
./run.sh

# Build only (no run)
./run.sh build

# Container (podman)
./run.sh podman          # build + run
./run.sh podman-build    # build only

# Tests
pytest tests/

# API docs (when running)
# Swagger: http://localhost:8000/api/docs
# Health:  http://localhost:8000/health
```

## Architecture

FastAPI app that synchronizes OpenShift cluster data from VLAN Manager (read-only) and manages manual cluster entries. No SQL database — uses file-based storage with in-memory caching.

**Layers (top → bottom):**
1. **API** (`src/api/routes.py`) — all endpoints, no business logic
2. **Services** (`src/services/`) — business logic, orchestration
3. **Data** (`src/database/store.py`) — file + in-memory storage with file locking
4. **Models** (`src/models/cluster.py`) — Pydantic validation
5. **Utils** (`src/utils/`) — validators, file I/O, logging; no upstream deps

**Key service areas:**
- `src/services/cluster/` — CRUD, DNS resolution, URL generation, merging
- `src/services/vlan/` — VLAN Manager API client, sync orchestrator, cache, transformer
- `src/services/export_service.py` — CSV/Excel export (pandas + openpyxl)
- `src/services/statistics_service.py` — analytics for dashboard

## Data Flow

```
VLAN Manager API → VLANApiClient → VLANDataTransformer → VLANCacheService → vlan_cache.json
                                                                              ↓
Manual clusters ──────────────────────────────────────────────────── manual_clusters.json
                                                                              ↓
                                                              ClusterService.get_combined_sites()
                                                              (VLAN takes precedence; manual fills gaps)
```

VLAN sync runs as a background task every 300s (configurable) via the FastAPI lifespan context manager in `src/main.py`.

## Configuration

Priority (highest to lowest): env vars → `config.json` → code defaults.

Key env vars: `LOG_LEVEL`, `VLAN_MANAGER_URL`, `DNS_SERVER`, `DNS_TIMEOUT`, `DNS_RESOLUTION_PATH`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `APP_TITLE`, `DEFAULT_DOMAIN`.

Config is loaded once as a singleton in `src/config.py`.

## Key Patterns

**Source tagging** — every cluster has `"source": "vlan-manager"` or `"source": "manual"`. Only manual clusters can be deleted via API.

**Singleton instances** — `Config`, `ClusterStore`, and `VLANSyncOrchestrator` are module-level singletons imported across the app.

**Thread-safe file I/O** — `src/utils/file_operations.py` uses `fcntl` locks + atomic temp-file rename; supports multi-replica pods sharing a PVC.

**Backward-compat wrappers** — `src/services/cluster_service.py`, `src/services/vlan_sync.py`, and `src/utils/cluster_utils.py` re-export from refactored modules. Prefer the canonical submodule paths for new code.

**Lazy imports** — some utils use deferred `from src.services...` imports inside functions to break circular dependencies.

**DNS resolution** — hostname template from config (default `ingress.{cluster_name}.{domain_name}`) is resolved via dnspython; supports multiple A records for round-robin.

## Authentication

HTTP Basic Auth on admin endpoints (`POST /api/clusters`, `DELETE /api/clusters/{id}`, `POST /api/vlan-sync/sync`). Credentials from env vars or `config.json`. See `src/auth.py`.

## Storage Files

- `data/manual_clusters.json` — user-created clusters
- `data/vlan_cache.json` — VLAN Manager sync cache
- `logs/app.log` — rotating log (10 MB × 5)

## Frontend

Vanilla JS + Jinja2 template (`src/templates/index.html`). Chart.js is vendored locally under `src/static/js/vendor/` for offline/air-gapped use.
