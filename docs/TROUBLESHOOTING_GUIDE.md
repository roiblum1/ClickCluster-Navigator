# Troubleshooting Guide
## OpenShift Cluster Navigator

Quick reference for common issues and how to resolve them.

---

## 🔍 Common Issues

### 1. Circular Import Errors

**Error**:
```
ImportError: cannot import name 'X' from partially initialized module 'src.Y'
```

**Cause**: Circular dependencies between modules

**Solution**:
- Use lazy imports (import inside functions)
- Review dependency graph
- Consider dependency inversion

**Example Fix**:
```python
# ❌ Bad - Import at module level
from src.services.cluster import IPResolverService

# ✅ Good - Lazy import
def my_function():
    from src.services.cluster import IPResolverService
    return IPResolverService.method()
```

---

### 2. DNS Resolution Not Working

**Symptoms**:
- LoadBalancer IPs showing as `null`
- DNS errors in logs

**Check**:
1. DNS server accessible?
   ```python
   # Check config.json
   "dns": {
     "server": "8.8.8.8",  # Is this reachable?
     "timeout_seconds": 3
   }
   ```

2. DNS resolution path correct?
   ```python
   # Check resolution path template
   "resolution_path": "ingress.{cluster_name}.{domain_name}"
   # For cluster "ocp4-test" and domain "example.com"
   # Resolves: ingress.ocp4-test.example.com
   ```

3. Check logs:
   ```bash
   # Look for DNS resolution logs
   grep "DNS" logs/app.log
   ```

**Solution**:
- Verify DNS server is reachable
- Check DNS resolution path matches your DNS setup
- Increase timeout if DNS is slow
- Check network connectivity from container

---

### 3. VLAN Manager Sync Failing

**Symptoms**:
- No clusters appearing
- "Connection error" in logs

**Check**:
1. VLAN Manager URL correct?
   ```python
   # config.json
   "vlan_manager": {
     "url": "http://vlan-manager:9000"  # Correct URL?
   }
   ```

2. VLAN Manager accessible?
   ```bash
   # Test connectivity
   curl http://vlan-manager:9000/api/segments
   ```

3. Check cache fallback:
   ```python
   # Application falls back to cache if API fails
   # Check: data/vlan_cache.json exists?
   ```

**Solution**:
- Verify VLAN Manager URL and connectivity
- Check network/firewall rules
- Application will use cached data if API unavailable
- Check `data/vlan_cache.json` for cached data

---

### 4. Cluster Not Appearing

**Symptoms**:
- Created cluster doesn't show up
- Cluster exists but not in list

**Check**:
1. Cluster name validation:
   ```python
   # Must start with "ocp4-"
   # Must be lowercase alphanumeric with hyphens
   cluster_name = "ocp4-test"  # ✅ Valid
   cluster_name = "test-cluster"  # ❌ Invalid (no ocp4- prefix)
   ```

2. Check source:
   ```python
   # Manual clusters: source = "manual"
   # VLAN clusters: source = "vlan-manager"
   # VLAN clusters take precedence
   ```

3. Check site filter:
   ```python
   # UI might be filtered by site
   # Check site dropdown in UI
   ```

**Solution**:
- Verify cluster name starts with "ocp4-"
- Check if cluster exists in VLAN Manager (takes precedence)
- Clear site filter in UI
- Check logs for creation errors

---

### 5. Multiple LoadBalancer IPs Not Showing

**Symptoms**:
- DNS returns multiple IPs but only one shows
- Round-robin IPs not displayed

**Check**:
1. DNS resolution returns list?
   ```python
   # Should return: ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
   # Not: "192.168.1.1"
   ```

2. UI handling list?
   ```javascript
   // Check app.js - should handle array
   const ipList = Array.isArray(cluster.loadBalancerIP) 
       ? cluster.loadBalancerIP 
       : [cluster.loadBalancerIP];
   ```

**Solution**:
- Verify DNS returns multiple A records
- Check UI code handles arrays correctly
- Check logs for DNS resolution results

---

### 6. Authentication Not Working

**Symptoms**:
- Can't access admin endpoints
- 401 Unauthorized errors

**Check**:
1. Credentials correct?
   ```python
   # Check config.json or environment variables
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=Password1
   ```

2. Using Basic Auth?
   ```bash
   # Test with curl
   curl -u admin:Password1 http://localhost:8000/api/clusters
   ```

**Solution**:
- Verify credentials in config or environment
- Use Basic Auth header: `Authorization: Basic <base64(username:password)>`
- Check `src/auth.py` for auth logic

---

### 7. File Locking Issues (Multi-Replica)

**Symptoms**:
- Cache write failures
- "Failed to save" errors

**Check**:
1. File permissions?
   ```bash
   # Check data directory permissions
   ls -la data/
   ```

2. Multiple replicas?
   ```python
   # File locking prevents concurrent writes
   # Check logs for lock timeouts
   ```

**Solution**:
- Ensure data directory is writable
- File locking handles concurrent access
- If issues persist, check file system supports locking
- Consider using database for production

---

### 8. Export Not Working

**Symptoms**:
- CSV/Excel export fails
- Empty exports

**Check**:
1. Dependencies installed?
   ```bash
   pip install pandas openpyxl
   ```

2. Data available?
   ```python
   # Export uses cluster_service.get_combined_sites()
   # Verify clusters exist
   ```

**Solution**:
- Install required packages: `pandas`, `openpyxl`
- Verify clusters exist before export
- Check logs for export errors

---

## 🐛 Debugging Tips

### 1. Enable Debug Logging

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or in config.json (not recommended for production)
# Use environment variables instead
```

### 2. Check Logs

```bash
# Application logs
tail -f logs/app.log

# Filter for errors
grep ERROR logs/app.log

# Filter for DNS
grep DNS logs/app.log

# Filter for sync
grep "sync" logs/app.log
```

### 3. Test DNS Resolution

```python
# Python script to test DNS
import dns.resolver

resolver = dns.resolver.Resolver()
resolver.nameservers = ['8.8.8.8']
answers = resolver.resolve('ingress.ocp4-test.example.com', 'A')
for answer in answers:
    print(answer)
```

### 4. Test VLAN Manager API

```bash
# Test segments endpoint
curl http://vlan-manager:9000/api/segments

# Test sites endpoint
curl http://vlan-manager:9000/api/sites

# Check response format
curl http://vlan-manager:9000/api/segments | jq .
```

### 5. Check Cache Files

```bash
# Manual clusters cache
cat data/manual_clusters.json | jq .

# VLAN Manager cache
cat data/vlan_cache.json | jq .

# Check last update time
jq '.last_updated' data/vlan_cache.json
```

---

## 🔧 Quick Fixes

### Reset Cache

```bash
# Backup first
cp data/manual_clusters.json data/manual_clusters.json.backup
cp data/vlan_cache.json data/vlan_cache.json.backup

# Clear cache (will be regenerated)
rm data/manual_clusters.json
rm data/vlan_cache.json
```

### Force Sync

```bash
# Trigger manual sync via API
curl -X POST http://localhost:8000/api/vlan-sync/sync

# Or restart application (auto-syncs on startup)
```

### Check Configuration

```python
# Python script to check config
from src.config import config

print(f"VLAN Manager URL: {config.vlan_manager_url}")
print(f"DNS Server: {config.dns_server}")
print(f"Default Domain: {config.default_domain}")
print(f"Sync Interval: {config.sync_interval}s")
```

---

## 📞 Getting Help

### Check Logs First
```bash
# Most issues are logged
tail -f logs/app.log
```

### Common Log Patterns

**DNS Issues**:
```
✗ DNS Failed: Timeout for ingress.ocp4-test.example.com
✗ DNS Failed: Name does not exist: ingress.ocp4-test.example.com
```

**VLAN Manager Issues**:
```
Connection error to /api/segments: All connection attempts failed
No segments fetched, attempting to load from cache...
```

**Validation Issues**:
```
Invalid cluster name 'test': Cluster name must start with 'ocp4-'
Invalid CIDR notation in segment '192.168.1': ...
```

### Useful Commands

```bash
# Check application health
curl http://localhost:8000/health

# Get all clusters
curl http://localhost:8000/api/clusters

# Get combined sites
curl http://localhost:8000/api/sites-combined

# Check sync status
curl http://localhost:8000/api/vlan-sync/status

# Get statistics
curl http://localhost:8000/api/statistics
```

---

## 🎯 Prevention

### Best Practices

1. **Always validate cluster names**:
   - Must start with "ocp4-"
   - Lowercase alphanumeric with hyphens

2. **Check DNS before creating clusters**:
   - Verify DNS resolution path
   - Test DNS resolution manually

3. **Monitor logs**:
   - Set up log monitoring
   - Watch for DNS failures
   - Monitor sync status

4. **Use environment variables**:
   - Don't hardcode credentials
   - Use config files for defaults
   - Override with environment variables

5. **Test in development first**:
   - Test DNS resolution
   - Test VLAN Manager connectivity
   - Verify configuration

---

**Last Updated**: 2025-01-XX

