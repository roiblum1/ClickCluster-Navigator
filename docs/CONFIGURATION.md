# OpenShift Cluster Navigator - Configuration Guide

## Configuration File

The application is configured via `config.json` in the root directory.

### config.json Structure

```json
{
  "vlan_manager": {
    "url": "http://0.0.0.0:9000",
    "sync_interval_seconds": 300
  },
  "application": {
    "host": "0.0.0.0",
    "port": 8000
  },
  "auth": {
    "admin_username": "admin",
    "admin_password": "Password1"
  }
}
```

## Configuration Options

### VLAN Manager Settings

**`vlan_manager.url`**
- Description: URL of the VLAN Manager API
- Default: `http://0.0.0.0:9000`
- Example: Change to `http://vlan-manager.example.com:9000` for production

**`vlan_manager.sync_interval_seconds`**
- Description: How often to automatically sync data from VLAN Manager
- Default: `300` (5 minutes)
- Recommendations:
  - Fast updates: `60` (1 minute)
  - Balanced: `180` (3 minutes)  
  - Conservative: `600` (10 minutes)

### Application Settings

**`application.host`**
- Description: Host address to bind the web server
- Default: `0.0.0.0` (all interfaces)
- Options:
  - `0.0.0.0` - Accessible from any network interface
  - `127.0.0.1` - Only accessible from localhost
  - `192.168.1.10` - Specific IP address

**`application.port`**
- Description: Port number for the web server
- Default: `8000`
- Example: Change to `9000`, `3000`, etc.

### Authentication Settings

**`auth.admin_username`**
- Description: Username for admin access
- Default: `admin`
- Security: Change this in production

**`auth.admin_password`**
- Description: Password for admin access
- Default: `Password1`
- Security: **Change this immediately in production!**

## Example Configurations

### Development Environment

```json
{
  "vlan_manager": {
    "url": "http://localhost:9000",
    "sync_interval_seconds": 60
  },
  "application": {
    "host": "127.0.0.1",
    "port": 8000
  },
  "auth": {
    "admin_username": "admin",
    "admin_password": "dev123"
  }
}
```

### Production Environment

```json
{
  "vlan_manager": {
    "url": "http://vlan-manager-prod.example.com:9000",
    "sync_interval_seconds": 300
  },
  "application": {
    "host": "0.0.0.0",
    "port": 8000
  },
  "auth": {
    "admin_username": "cluster_admin",
    "admin_password": "Str0ng!Pass#2024"
  }
}
```

### Testing with Different VLAN Manager

```json
{
  "vlan_manager": {
    "url": "http://test-vlan-api.example.com:8080",
    "sync_interval_seconds": 120
  },
  "application": {
    "host": "0.0.0.0",
    "port": 8000
  },
  "auth": {
    "admin_username": "admin",
    "admin_password": "Test123"
  }
}
```

## Applying Configuration Changes

1. Edit `config.json`
2. Save the file
3. Restart the application:
   ```bash
   # Stop the current server (Ctrl+C)
   # Start again
   python -m src.main
   ```

The configuration is loaded at startup and displayed in the console:
```
✓ Configuration loaded from /path/to/config.json
```

## Configuration Verification

After starting the app, verify configuration was loaded:

1. Check console output for:
   ```
   ✓ Configuration loaded from .../config.json
   INFO:src.services.vlan_sync:VLAN sync service started (interval: 300s, URL: http://0.0.0.0:9000)
   ```

2. Login as admin and check the Admin Control Panel for:
   - Data Source URL
   - Sync interval
   - Last sync time

## Security Best Practices

1. **Change default credentials**
   - Never use `admin/Password1` in production
   - Use strong passwords (12+ characters, mixed case, numbers, symbols)

2. **Restrict network access**
   - Use `127.0.0.1` if only local access needed
   - Configure firewall rules for production

3. **HTTPS in production**
   - Use a reverse proxy (nginx, Apache) with SSL/TLS
   - Never transmit credentials over plain HTTP in production

4. **Secure config file**
   ```bash
   chmod 600 config.json  # Only owner can read/write
   ```

## Troubleshooting

### Config not loading

**Problem**: Application uses default values

**Solution**:
1. Ensure `config.json` is in the root directory (same level as `src/`)
2. Check file has valid JSON syntax
3. Review console output for error messages

### VLAN Manager connection fails

**Problem**: Sync errors in logs

**Solution**:
1. Verify `vlan_manager.url` is correct
2. Test URL manually:
   ```bash
   curl http://YOUR_URL/api/segments?allocated=true
   ```
3. Check VLAN Manager is running
4. Verify network connectivity

### Authentication not working

**Problem**: Login fails with correct credentials

**Solution**:
1. Restart application after changing `config.json`
2. Clear browser session storage
3. Check credentials match exactly (case-sensitive)

## Environment Variables (Future Enhancement)

Currently, configuration is file-based. For environment variable support, create a feature request.

Example future usage:
```bash
export VLAN_MANAGER_URL="http://prod-vlan:9000"
export ADMIN_PASSWORD="SecurePass123"
python -m src.main
```
