# OpenShift Cluster Navigator

A web application for managing and navigating OpenShift clusters organized by deployment sites.

## Features

- **Cluster Management**: Add, view, and delete OpenShift clusters
- **Site Organization**: Clusters are automatically organized by deployment site
- **Network Segments**: Track network segments (CIDR) for each cluster
- **Quick Navigation**: One-click access to OpenShift console for any cluster
- **Validation**: Built-in validation for cluster names and CIDR notation
- **Modern UI**: Responsive design with a clean, professional interface

## Architecture

```
ClickCluster-Navigator/
├── src/
│   ├── api/                 # FastAPI route handlers
│   │   ├── clusters.py      # Cluster CRUD endpoints
│   │   └── sites.py         # Site organization endpoints
│   ├── database/            # Data storage layer
│   │   └── store.py         # In-memory data store
│   ├── models/              # Pydantic models
│   │   └── cluster.py       # Data models with validation
│   ├── static/              # Frontend static files
│   │   ├── css/
│   │   │   └── style.css    # Application styles
│   │   └── js/
│   │       └── app.js       # Frontend JavaScript
│   ├── templates/           # HTML templates
│   │   └── index.html       # Main UI page
│   └── main.py              # FastAPI application entry point
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container configuration
└── README.md               # This file
```

## Requirements

- Python 3.11+
- Podman (optional, for containerized deployment)

## Installation & Deployment

### Quick Start - Local Development

```bash
./run.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Start the application on [http://localhost:8000](http://localhost:8000)

### Quick Start - Podman Deployment

```bash
./run.sh podman
```

This will:
- Build the container image
- Start the container with health checks
- Expose the application on [http://localhost:8000](http://localhost:8000)

### Manual Local Development

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python -m src.main
   ```

4. Open your browser to [http://localhost:8000](http://localhost:8000)

### Manual Podman Deployment

1. Build the image:
   ```bash
   podman build -t openshift-cluster-navigator .
   ```

2. Run the container:
   ```bash
   podman run -d \
     --name cluster-navigator \
     -p 8000:8000 \
     --health-cmd='python -c "import urllib.request; urllib.request.urlopen(\"http://localhost:8000/health\")"' \
     --health-interval=30s \
     --health-timeout=10s \
     --health-retries=3 \
     openshift-cluster-navigator
   ```

3. Access the application at [http://localhost:8000](http://localhost:8000)

### Accessing the Application

- **UI**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

## API Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **ReDoc**: [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)

### API Endpoints

#### Clusters

- `POST /api/clusters` - Create a new cluster
- `GET /api/clusters` - Get all clusters
- `GET /api/clusters/{cluster_id}` - Get cluster by ID
- `GET /api/clusters/name/{cluster_name}` - Get cluster by name
- `PATCH /api/clusters/{cluster_id}` - Update cluster
- `DELETE /api/clusters/{cluster_id}` - Delete cluster
- `GET /api/clusters/site/{site_name}` - Get clusters by site

#### Sites

- `GET /api/sites` - Get all sites with their clusters
- `GET /api/sites/{site_name}` - Get specific site with clusters

### Example API Request

```bash
curl -X POST "http://localhost:8000/api/clusters" \
  -H "Content-Type: application/json" \
  -d '{
    "clusterName": "ocp4-roi",
    "site": "site1",
    "segments": ["192.178.1.0/24", "192.178.2.0/24"],
    "domainName": "example.com"
  }'
```

## Data Model

### Cluster

```json
{
  "clusterName": "ocp4-roi",
  "site": "site1",
  "segments": ["192.178.1.0/24", "192.178.2.0/24"],
  "domainName": "example.com"
}
```

**Validation Rules:**
- `clusterName`: Lowercase alphanumeric with hyphens, 3-100 characters
- `site`: Required, 1-50 characters
- `segments`: Array of valid CIDR notation (e.g., 192.178.1.0/24)
- `domainName`: Optional, defaults to "example.com"

## Features in Detail

### Pydantic Validation

The application uses Pydantic for robust data validation:
- **Cluster Name**: Validates format (lowercase, alphanumeric, hyphens)
- **CIDR Validation**: Ensures all network segments are valid CIDR notation
- **Type Safety**: Automatic type checking and conversion

### Console URL Generation

For each cluster, the application automatically generates the OpenShift console URL:
```
https://console-openshift-console.<cluster-name>.apps.<domain-name>
```

### Site Organization

Clusters are automatically grouped by their deployment site, making it easy to navigate large deployments across multiple locations.

## Development

### Running Tests

```bash
pytest tests/
```

### Code Structure

- **Models** ([src/models/cluster.py](src/models/cluster.py)): Pydantic models with validation
- **API Routes** ([src/api/](src/api/)): FastAPI endpoints organized by resource
- **Database** ([src/database/store.py](src/database/store.py)): In-memory storage (easily replaceable with SQL)
- **Frontend** ([src/static/](src/static/), [src/templates/](src/templates/)): HTML/CSS/JS interface

### Extending the Application

To add a database backend (e.g., PostgreSQL):

1. Install SQLAlchemy:
   ```bash
   pip install sqlalchemy psycopg2-binary
   ```

2. Replace [src/database/store.py](src/database/store.py) with SQLAlchemy models and sessions

3. Update the API routes to use database sessions

## Security Considerations

- Input validation using Pydantic
- XSS protection with HTML escaping
- CORS configuration (update for production)
- Non-root user in Docker container
- Health checks for monitoring

## License

MIT License

## Contributing

Contributions are welcome! Please ensure:
- Code follows the existing structure
- Pydantic models include proper validation
- API endpoints include proper error handling
- Frontend is responsive and accessible
