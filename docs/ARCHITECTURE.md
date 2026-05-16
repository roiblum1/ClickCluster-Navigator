# Architecture & SOLID Principles

## Overview

The OpenShift Cluster Navigator application follows SOLID principles and clean architecture patterns. This document outlines how the codebase adheres to these principles.

## SOLID Principles Compliance

### ✅ Single Responsibility Principle (SRP)

Each class/module has one clear responsibility:

**API Layer (`src/api/`):**
- `clusters.py` - HTTP endpoints for cluster operations only
- `combined.py` - HTTP endpoints for combined data only
- `vlan_sync.py` - HTTP endpoints for sync operations only
- `statistics.py` - HTTP endpoints for statistics only
- `export.py` - HTTP endpoints for data export only

**Service Layer (`src/services/`):**
- `cluster_service.py` - Business logic for cluster operations
- `vlan_sync.py` - VLAN Manager synchronization logic

**Data Layer (`src/database/`):**
- `store.py` - Data persistence and retrieval only

**Models (`src/models/`):**
- `cluster.py` - Data validation and structure only

**Utils (`src/utils/`):**
- `cluster_utils.py` - Cluster-related utilities (URL generation, IP resolution)
- `cluster_validator.py` - Validation logic only
- `file_operations.py` - File I/O operations only

### ✅ Open/Closed Principle (OCP)

The code is open for extension but closed for modification:

**Configuration System:**
```python
# Easy to extend via environment variables or config.json
# No code changes required for new configuration
config.dns_resolution_path  # Configurable DNS path
config.default_domain       # Configurable domain
```

**Service Layer Pattern:**
```python
# ClusterService can be extended with new methods
# without modifying existing code
class ClusterService:
    def get_combined_sites(self): ...
    def create_manual_cluster(self): ...
    # New methods can be added without breaking existing ones
```

**Exception Hierarchy:**
```python
# New exceptions can be added without modifying handlers
class ClusterException(Exception): pass
class ClusterNotFoundError(ClusterException): pass
# Easy to add new specific exceptions
```

### ✅ Liskov Substitution Principle (LSP)

Interfaces and base classes can be substituted:

**Exception Hierarchy:**
```python
# All custom exceptions can be caught as ClusterException
try:
    # ...
except ClusterException as e:
    # Handles all cluster-related exceptions
```

**Response Models:**
```python
# All response models follow BaseModel contract
class ClusterResponse(BaseModel): ...
class SiteResponse(BaseModel): ...
# Can be used interchangeably where BaseModel is expected
```

### ✅ Interface Segregation Principle (ISP)

Clients only depend on methods they use:

**Service Layer:**
```python
# API layer only uses methods it needs
cluster_service.get_combined_sites()      # Used by combined.py
cluster_service.create_manual_cluster()   # Used by clusters.py
cluster_service.delete_manual_cluster()   # Used by clusters.py
```

**Utils:**
```python
# Each utility class has specific, focused methods
ClusterUtils.generate_console_url()
ClusterUtils.resolve_loadbalancer_ip()
ClusterValidator.validate_cluster_name()
FileOperations.read_json_with_lock()
```

### ✅ Dependency Inversion Principle (DIP)

High-level modules don't depend on low-level modules:

**Layered Architecture:**
```
API Layer (clusters.py)
    ↓ depends on
Service Layer (cluster_service.py)
    ↓ depends on
Data Layer (store.py)
```

**Dependency Injection:**
```python
# Routes depend on abstractions (service instances)
# Not concrete implementations
from src.services.cluster_service import cluster_service

@router.post("/")
async def create_cluster(cluster_data: ClusterCreate):
    cluster = cluster_service.create_manual_cluster(cluster_dict)
```

**Configuration Abstraction:**
```python
# Code depends on config interface, not implementation
from src.config import config

# Config can be loaded from file, env, or other sources
# without changing dependent code
```

## Architecture Layers

### 1. **API Layer** (`src/api/`)
- **Responsibility:** HTTP request/response handling
- **Dependencies:** Service layer, models
- **No direct access to:** Database, file system

### 2. **Service Layer** (`src/services/`)
- **Responsibility:** Business logic, orchestration
- **Dependencies:** Data layer, utils
- **No direct access to:** HTTP layer

### 3. **Data Layer** (`src/database/`)
- **Responsibility:** Data persistence
- **Dependencies:** Utils (file operations)
- **No direct access to:** HTTP, business logic

### 4. **Models Layer** (`src/models/`)
- **Responsibility:** Data validation, structure
- **Dependencies:** Utils (validators)
- **No direct access to:** HTTP, services, database

### 5. **Utils Layer** (`src/utils/`)
- **Responsibility:** Reusable utilities
- **Dependencies:** Config only
- **No direct access to:** HTTP, services, database

## Design Patterns Used

### 1. **Service Layer Pattern**
Separates business logic from API endpoints:
```python
# API layer delegates to service
cluster_service.create_manual_cluster(cluster_dict)
```

### 2. **Repository Pattern**
Data access abstraction:
```python
# ClusterStore abstracts data persistence
cluster_store.create_cluster(data)
cluster_store.get_cluster(id)
```

### 3. **Singleton Pattern**
Global service instances:
```python
# Global instances for shared resources
config = Config()
cluster_service = ClusterService()
vlan_sync_service = VLANSyncService()
```

### 4. **Factory Pattern**
Object creation in utilities:
```python
# ClusterUtils creates URLs
ClusterUtils.generate_console_url(name, domain)
```

### 5. **Strategy Pattern**
DNS resolution path is configurable:
```python
# Resolution strategy can be changed via config
hostname = config.dns_resolution_path.format(...)
```

## Code Quality Metrics

### Separation of Concerns
- ✅ API logic separated from business logic
- ✅ Business logic separated from data access
- ✅ Validation separated from models
- ✅ Utilities are reusable and focused

### No Code Duplication
- ✅ Console URL generation centralized in `ClusterUtils`
- ✅ Cluster validation centralized in `ClusterValidator`
- ✅ File operations centralized in `FileOperations`
- ✅ Site grouping logic centralized in `SiteUtils`

### Testability
- ✅ Each layer can be tested independently
- ✅ Service layer can be mocked in API tests
- ✅ Data layer can be mocked in service tests
- ✅ Utils have no dependencies (easy to unit test)

### Maintainability
- ✅ Changes to one layer don't affect others
- ✅ New features can be added without modifying existing code
- ✅ Configuration changes don't require code changes
- ✅ Clear module boundaries

## File Structure

```
src/
├── api/              # API endpoints (HTTP layer)
│   ├── clusters.py   # Cluster CRUD endpoints
│   ├── combined.py   # Combined data endpoints
│   ├── vlan_sync.py  # Sync endpoints
│   ├── statistics.py # Statistics endpoints
│   └── export.py     # Export endpoints
│
├── services/         # Business logic layer
│   ├── cluster_service.py   # Cluster operations
│   └── vlan_sync.py         # VLAN sync operations
│
├── database/         # Data persistence layer
│   └── store.py      # In-memory/file storage
│
├── models/           # Data models & validation
│   └── cluster.py    # Pydantic models
│
├── utils/            # Reusable utilities
│   ├── cluster_utils.py      # Cluster utilities
│   └── file_operations.py    # File I/O utilities
│
├── config.py         # Configuration management
├── auth.py           # Authentication
├── exceptions.py     # Custom exceptions
└── main.py           # Application entry point
```

## Benefits of Current Architecture

### 1. **Scalability**
- Easy to add new endpoints
- Easy to add new business logic
- Easy to change data storage (e.g., switch to SQL)

### 2. **Maintainability**
- Clear boundaries between layers
- Changes are localized
- Easy to understand code flow

### 3. **Testability**
- Each layer can be tested independently
- Easy to mock dependencies
- Utils have no side effects

### 4. **Flexibility**
- Configuration can be changed without code changes
- Business logic can evolve without API changes
- Data storage can be swapped without service changes

### 5. **Reusability**
- Utils are reusable across the application
- Service layer can be used by multiple API endpoints
- Models enforce consistent validation

## Multi-Replica Safety

### File Locking (`FileOperations`)
- **Shared locks** for concurrent reads
- **Exclusive locks** for writes
- **Atomic writes** with temp file + rename
- **Retry logic** with exponential backoff

### Concurrency Considerations
- ✅ Thread-safe file operations
- ✅ No shared mutable state
- ✅ Independent replica instances
- ✅ File-based coordination

## Security

### Authentication
- HTTP Basic Auth for admin endpoints
- Credentials configurable via env/config
- Protected DELETE and POST endpoints

### Input Validation
- Pydantic models for all inputs
- CIDR notation validation
- IPv4 address validation
- Cluster name pattern validation

### Data Protection
- Read-only VLAN Manager access (GET only)
- VLAN Manager clusters protected from deletion
- Manual clusters isolated from synced data

## Configuration Management

### Hierarchical Configuration
1. **Default values** in code
2. **config.json** file
3. **Environment variables** (highest priority)

### Configurable Values
- VLAN Manager URL
- Default domain
- DNS server and timeout
- DNS resolution path template
- Admin credentials
- Application title
- Sync interval

### Environment Variables
- `VLAN_MANAGER_URL`
- `DEFAULT_DOMAIN`
- `DNS_SERVER`
- `DNS_TIMEOUT`
- `DNS_RESOLUTION_PATH`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `APP_TITLE`

## Next Architectural Improvements (Optional)

### 1. **Database Abstraction**
Consider adding a repository interface if switching to SQL:
```python
class IClusterRepository(ABC):
    @abstractmethod
    def get_cluster(self, id: str): pass
    @abstractmethod
    def create_cluster(self, data: dict): pass
```

### 2. **Dependency Injection Framework**
Consider using a DI framework for better testability:
```python
# Currently: global instances
# Future: injected dependencies
def __init__(self, cluster_store: IClusterRepository):
    self.cluster_store = cluster_store
```

### 3. **Event System**
Consider adding events for better decoupling:
```python
# Emit events when clusters are created/deleted
event_bus.emit("cluster.created", cluster_data)
```

### 4. **CQRS Pattern**
Consider separating read and write operations:
```python
# Command: create_manual_cluster()
# Query: get_combined_sites()
```

## Conclusion

The codebase demonstrates strong adherence to SOLID principles with:
- Clear separation of concerns
- Minimal coupling between layers
- High cohesion within modules
- Easy to test, maintain, and extend
- Production-ready architecture
