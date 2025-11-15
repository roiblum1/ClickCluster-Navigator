# Environment Variables Configuration

This document describes the environment variables that can be used to configure the OpenShift Cluster Navigator application.

## Available Environment Variables

### Application Configuration

#### `APP_TITLE`
- **Description**: The title displayed in the application header and browser tab
- **Default**: `"OpenShift Cluster Navigator"`
- **Example**: `APP_TITLE="Red Bull Racing Cluster Navigator"`

### Authentication Configuration

#### `ADMIN_USERNAME`
- **Description**: The username for admin authentication
- **Default**: `"admin"`
- **Example**: `ADMIN_USERNAME="cluster-admin"`

#### `ADMIN_PASSWORD`
- **Description**: The password for admin authentication
- **Default**: `"Password1"`
- **Example**: `ADMIN_PASSWORD="SecurePassword123!"`
- **Security Note**: Always use strong passwords in production environments

## Usage

### Docker/Podman

When running the container, pass environment variables using the `-e` flag:

```bash
podman run -d \
  --name cluster-navigator \
  -p 8000:8000 \
  -e APP_TITLE="My Custom Title" \
  -e ADMIN_USERNAME="myadmin" \
  -e ADMIN_PASSWORD="MySecurePassword123!" \
  openshift-cluster-navigator
```

Or using an environment file:

```bash
# Create .env file
cat > .env <<EOF
APP_TITLE=Red Bull Racing Cluster Navigator
ADMIN_USERNAME=rbr-admin
ADMIN_PASSWORD=SecurePass2024!
EOF

# Run with env file
podman run -d \
  --name cluster-navigator \
  -p 8000:8000 \
  --env-file .env \
  openshift-cluster-navigator
```

### Local Development

Set environment variables before running the application:

```bash
# Linux/macOS
export APP_TITLE="Development Cluster Navigator"
export ADMIN_USERNAME="dev-admin"
export ADMIN_PASSWORD="DevPassword123"
python -m src.main

# Or inline
APP_TITLE="Dev Navigator" ADMIN_USERNAME="admin" python -m src.main
```

```powershell
# Windows PowerShell
$env:APP_TITLE="Development Cluster Navigator"
$env:ADMIN_USERNAME="dev-admin"
$env:ADMIN_PASSWORD="DevPassword123"
python -m src.main
```

### Kubernetes/OpenShift Deployment

Use ConfigMap and Secrets for configuration:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-navigator-config
data:
  APP_TITLE: "Production Cluster Navigator"
  ADMIN_USERNAME: "prod-admin"
---
apiVersion: v1
kind: Secret
metadata:
  name: cluster-navigator-secret
type: Opaque
stringData:
  ADMIN_PASSWORD: "ProductionSecurePassword123!"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-navigator
spec:
  template:
    spec:
      containers:
      - name: app
        image: openshift-cluster-navigator:latest
        envFrom:
        - configMapRef:
            name: cluster-navigator-config
        env:
        - name: ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: cluster-navigator-secret
              key: ADMIN_PASSWORD
```

## Configuration Priority

The application reads configuration in the following priority order:

1. **Environment Variables** (highest priority)
2. **config.json file**
3. **Default values** (lowest priority)

This means environment variables will override values in `config.json`.

## Security Best Practices

1. **Never commit credentials to version control**
   - Add `.env` to `.gitignore`
   - Use secrets management for production

2. **Use strong passwords**
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, and symbols
   - Avoid common words and patterns

3. **Rotate credentials regularly**
   - Change admin password periodically
   - Update secrets in your deployment

4. **Limit access**
   - Only share admin credentials with authorized personnel
   - Consider implementing role-based access control (RBAC) for multi-user scenarios

## Troubleshooting

### Environment variable not taking effect

1. Check that the variable is properly set:
   ```bash
   echo $APP_TITLE
   ```

2. Restart the application after setting environment variables

3. For Docker/Podman, ensure the container is restarted:
   ```bash
   podman restart cluster-navigator
   ```

### Authentication failing after changing credentials

1. Clear browser cache and cookies
2. Verify the new credentials are correctly set
3. Check application logs for authentication errors:
   ```bash
   podman logs cluster-navigator
   ```
