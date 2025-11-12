# Nginx Configuration Fix for 404 Error on siufu-api.tinsu.ai

## Problem Summary

After changing the backend domain from `api.siufu.tinsu.ai` to `siufu-api.tinsu.ai`, the frontend is getting 404 errors when trying to access the API:

```
POST https://siufu-api.tinsu.ai/auth/login 404 (Not Found)
```

**Root Cause**: The Nginx reverse proxy on the production server is not configured for the new domain `siufu-api.tinsu.ai`. The backend Docker container is running correctly (internal health check passes), but external HTTPS requests to `siufu-api.tinsu.ai` are returning 404 because Nginx doesn't have a server block configured for this domain.

## Required Actions on Production Server

### Step 1: Verify Current Nginx Configuration

SSH into the production server and check existing Nginx sites:

```bash
# SSH into production server
ssh your-user@your-server-ip

# List enabled Nginx sites
ls -la /etc/nginx/sites-enabled/

# Check if siufu-api.tinsu.ai configuration exists
ls -la /etc/nginx/sites-available/siufu-api.tinsu.ai
```

### Step 2: Create Nginx Configuration for Backend API

If the configuration doesn't exist, create it:

```bash
sudo nano /etc/nginx/sites-available/siufu-api.tinsu.ai
```

Paste the following configuration:

```nginx
# Upstream definition for backend API
upstream backend_upstream {
    server localhost:8780;
    keepalive 32;
}

# HTTP to HTTPS redirect for API
server {
    listen 80;
    listen [::]:80;
    server_name siufu-api.tinsu.ai;

    # Allow Cloudflare SSL verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect all other HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server for backend API
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name siufu-api.tinsu.ai;

    # SSL Configuration (Cloudflare Origin Certificate)
    ssl_certificate /etc/nginx/ssl/siufu.tinsu.ai.pem;
    ssl_certificate_key /etc/nginx/ssl/siufu.tinsu.ai.key;

    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Cloudflare Real IP Configuration
    set_real_ip_from 173.245.48.0/20;
    set_real_ip_from 103.21.244.0/22;
    set_real_ip_from 103.22.200.0/22;
    set_real_ip_from 103.31.4.0/22;
    set_real_ip_from 141.101.64.0/18;
    set_real_ip_from 108.162.192.0/18;
    set_real_ip_from 190.93.240.0/20;
    set_real_ip_from 188.114.96.0/20;
    set_real_ip_from 197.234.240.0/22;
    set_real_ip_from 198.41.128.0/17;
    set_real_ip_from 162.158.0.0/15;
    set_real_ip_from 104.16.0.0/13;
    set_real_ip_from 104.24.0.0/14;
    set_real_ip_from 172.64.0.0/13;
    set_real_ip_from 131.0.72.0/22;
    set_real_ip_from 2400:cb00::/32;
    set_real_ip_from 2606:4700::/32;
    set_real_ip_from 2803:f800::/32;
    set_real_ip_from 2405:b500::/32;
    set_real_ip_from 2405:8100::/32;
    set_real_ip_from 2a06:98c0::/29;
    set_real_ip_from 2c0f:f248::/32;
    real_ip_header CF-Connecting-IP;

    # Max upload size (for file uploads)
    client_max_body_size 50M;

    # Logging
    access_log /var/log/nginx/siufu.api.access.log;
    error_log /var/log/nginx/siufu.api.error.log;

    # Backend API - All routes
    location / {
        proxy_pass http://backend_upstream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### Step 3: Verify SSL Certificates

The configuration above uses the same SSL certificate as the main domain. If you're using a wildcard certificate, you can create symlinks:

```bash
# Check if SSL certificates exist
ls -la /etc/nginx/ssl/siufu.tinsu.ai.pem
ls -la /etc/nginx/ssl/siufu.tinsu.ai.key

# If they exist, create symlinks for the API domain (if not already present)
sudo ln -sf /etc/nginx/ssl/siufu.tinsu.ai.pem /etc/nginx/ssl/siufu-api.tinsu.ai.pem
sudo ln -sf /etc/nginx/ssl/siufu.tinsu.ai.key /etc/nginx/ssl/siufu-api.tinsu.ai.key

# Verify symlinks
ls -la /etc/nginx/ssl/
```

**Note**: If you don't have a wildcard certificate, you'll need to create a new Cloudflare Origin Certificate that includes `siufu-api.tinsu.ai` as one of the hostnames. See the "SSL Certificate Setup" section below.

### Step 4: Enable the Site

```bash
# Create symlink to enable the site
sudo ln -sf /etc/nginx/sites-available/siufu-api.tinsu.ai /etc/nginx/sites-enabled/

# Verify symlink was created
ls -la /etc/nginx/sites-enabled/
```

### Step 5: Test Nginx Configuration

```bash
# Test configuration for syntax errors
sudo nginx -t

# Expected output:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

If you see any errors, review the configuration file and fix any typos.

### Step 6: Reload Nginx

```bash
# Reload Nginx to apply the new configuration
sudo systemctl reload nginx

# Check Nginx status
sudo systemctl status nginx

# Expected: Active (running)
```

### Step 7: Verify DNS and Cloudflare Configuration

Make sure the DNS A record exists in Cloudflare:

1. Log into Cloudflare Dashboard
2. Select domain: `tinsu.ai`
3. Go to DNS → Records
4. Verify the following A record exists:
   - **Type**: A
   - **Name**: `siufu-api`
   - **Content**: Your server IP address
   - **Proxy status**: Proxied (orange cloud)
   - **TTL**: Auto

If it doesn't exist, create it:

```
Type: A
Name: siufu-api
IPv4 address: <your-server-ip>
Proxy status: Proxied (orange cloud enabled)
TTL: Auto
```

### Step 8: Test the API Endpoint

From your local machine or any external location:

```bash
# Test health endpoint
curl -v https://siufu-api.tinsu.ai/health

# Expected response:
# HTTP/2 200 OK
# {"status":"healthy"} or similar

# Test login endpoint (should return 422 or similar, not 404)
curl -v -X POST https://siufu-api.tinsu.ai/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# Expected: NOT 404, should be 422 (validation error) or 401 (unauthorized)
```

### Step 9: Check Nginx Logs

If you still get 404 errors, check the Nginx logs:

```bash
# Check error logs for siufu-api
sudo tail -f /var/log/nginx/siufu.api.error.log

# Check access logs
sudo tail -f /var/log/nginx/siufu.api.access.log

# If no logs appear, check the default error log
sudo tail -f /var/log/nginx/error.log
```

### Step 10: Verify Backend Container is Running

Make sure the backend container is accessible:

```bash
cd ~/logai-production

# Check container status
docker compose -f docker-compose.prod.yml ps

# Test internal backend health check
docker compose -f docker-compose.prod.yml exec backend curl http://localhost:8000/health

# Check backend logs
docker compose -f docker-compose.prod.yml logs backend --tail=50
```

## SSL Certificate Setup (If Needed)

If you need to create a new SSL certificate for the API domain:

### Option 1: Use Existing Wildcard Certificate

If you already have a wildcard certificate for `*.tinsu.ai`, you can use it for both domains:

1. The certificate should include hostnames:
   - `*.tinsu.ai`
   - `tinsu.ai`

2. This covers both `siufu.tinsu.ai` and `siufu-api.tinsu.ai`

3. Use symlinks (as shown in Step 3 above)

### Option 2: Create New Cloudflare Origin Certificate

If you need a new certificate:

1. Go to Cloudflare Dashboard
2. Select domain: `tinsu.ai`
3. Navigate to: **SSL/TLS → Origin Server**
4. Click: **Create Certificate**
5. Choose: "Generate private key and CSR with Cloudflare"
6. Add hostnames:
   - `siufu.tinsu.ai`
   - `siufu-api.tinsu.ai`
7. Select validity period: 15 years (recommended)
8. Click: **Create**
9. Copy the certificate and private key
10. Save to server:

```bash
# Save certificate
sudo nano /etc/nginx/ssl/siufu-api.tinsu.ai.pem
# Paste the Origin Certificate

# Save private key
sudo nano /etc/nginx/ssl/siufu-api.tinsu.ai.key
# Paste the Private Key

# Set proper permissions
sudo chmod 600 /etc/nginx/ssl/siufu-api.tinsu.ai.key
sudo chmod 644 /etc/nginx/ssl/siufu-api.tinsu.ai.pem
```

11. Update the Nginx configuration to use the new certificate paths:

```nginx
ssl_certificate /etc/nginx/ssl/siufu-api.tinsu.ai.pem;
ssl_certificate_key /etc/nginx/ssl/siufu-api.tinsu.ai.key;
```

## Verification Checklist

After completing all steps, verify:

- [ ] Nginx configuration file created: `/etc/nginx/sites-available/siufu-api.tinsu.ai`
- [ ] Symlink created: `/etc/nginx/sites-enabled/siufu-api.tinsu.ai`
- [ ] SSL certificates exist and have correct permissions
- [ ] `sudo nginx -t` passes without errors
- [ ] Nginx reloaded: `sudo systemctl reload nginx`
- [ ] Cloudflare DNS A record exists for `siufu-api` with proxy enabled
- [ ] Backend container is running: `docker compose -f docker-compose.prod.yml ps`
- [ ] Internal health check works: `curl http://localhost:8780/health`
- [ ] External health check works: `curl https://siufu-api.tinsu.ai/health`
- [ ] Frontend can access API: Test login from https://siufu.tinsu.ai
- [ ] No 404 errors in browser console

## Troubleshooting

### Issue: "Connection refused" from curl

**Cause**: Nginx can't connect to backend on localhost:8780

**Solution**:
```bash
# Check if backend is listening on 8780
sudo netstat -tlnp | grep 8780
# or
sudo ss -tlnp | grep 8780

# Check Docker port mapping
docker compose -f docker-compose.prod.yml ps
# Should show: 0.0.0.0:8780->8000/tcp
```

### Issue: Still getting 404 after configuration

**Possible causes**:
1. Nginx configuration not loaded properly
2. Server name mismatch
3. Cloudflare DNS not propagated
4. SSL certificate issue

**Debug steps**:
```bash
# Check if Nginx is listening on 443
sudo netstat -tlnp | grep :443

# Check which Nginx config files are loaded
sudo nginx -T | grep server_name

# Look for siufu-api.tinsu.ai in the output

# Test DNS resolution
nslookup siufu-api.tinsu.ai
dig siufu-api.tinsu.ai

# Check Nginx error logs
sudo tail -100 /var/log/nginx/error.log | grep siufu-api
```

### Issue: SSL certificate errors

**Solution**:
```bash
# Verify certificate is valid
openssl x509 -in /etc/nginx/ssl/siufu-api.tinsu.ai.pem -text -noout | grep -A2 "Subject:"

# Check certificate expiration
openssl x509 -in /etc/nginx/ssl/siufu-api.tinsu.ai.pem -noout -enddate

# Verify private key matches certificate
openssl x509 -noout -modulus -in /etc/nginx/ssl/siufu-api.tinsu.ai.pem | openssl md5
openssl rsa -noout -modulus -in /etc/nginx/ssl/siufu-api.tinsu.ai.key | openssl md5
# The hashes should match
```

### Issue: Cloudflare shows "Error 521"

**Cause**: Origin server is not responding or SSL handshake failed

**Solution**:
1. Verify Nginx is running: `sudo systemctl status nginx`
2. Check if port 443 is open: `sudo ufw status`
3. Ensure SSL/TLS mode in Cloudflare is set to "Full (strict)"
4. Verify Origin Certificate is installed correctly

### Issue: Backend returns errors

**Solution**:
```bash
# Check backend logs
cd ~/logai-production
docker compose -f docker-compose.prod.yml logs backend --tail=100

# Check if CORS is configured correctly
docker compose -f docker-compose.prod.yml exec backend env | grep CORS

# Expected: CORS_ORIGINS should include https://siufu.tinsu.ai
```

## Quick Reference Commands

```bash
# SSH into server
ssh your-user@your-server-ip

# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# View Nginx logs
sudo tail -f /var/log/nginx/siufu.api.error.log
sudo tail -f /var/log/nginx/siufu.api.access.log

# Check backend container
cd ~/logai-production
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs backend --tail=50

# Test internal health
docker compose -f docker-compose.prod.yml exec backend curl http://localhost:8000/health

# Test external health
curl -v https://siufu-api.tinsu.ai/health

# Check DNS
nslookup siufu-api.tinsu.ai

# Check listening ports
sudo netstat -tlnp | grep -E '(8780|443)'
```

## Additional Notes

1. **Port Mapping**: The backend container exposes port 8000 internally, which is mapped to port 8780 on the host. Nginx proxies from port 443 (HTTPS) to localhost:8780.

2. **Cloudflare SSL Mode**: Make sure Cloudflare SSL/TLS mode is set to "Full (strict)" for proper end-to-end encryption.

3. **DNS Propagation**: If you just created the DNS record, it may take a few minutes to propagate, although Cloudflare is usually instant.

4. **Firewall**: Ensure ports 80 and 443 are allowed through the firewall (UFW or iptables).

5. **SELinux**: If your server uses SELinux (common on CentOS/RHEL), you may need to configure it to allow Nginx to connect to network ports:
   ```bash
   sudo setsebool -P httpd_can_network_connect 1
   ```

## Success Indicators

When everything is working correctly, you should see:

1. **Nginx test passes**:
   ```
   $ sudo nginx -t
   nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
   nginx: configuration file /etc/nginx/nginx.conf test is successful
   ```

2. **External API health check succeeds**:
   ```
   $ curl https://siufu-api.tinsu.ai/health
   {"status":"healthy"}
   ```

3. **Frontend can authenticate**:
   - Open https://siufu.tinsu.ai in browser
   - Try to log in
   - No 404 errors in console
   - Login request goes to https://siufu-api.tinsu.ai/auth/login

4. **CI workflow shows**:
   ```
   External API health check: PASSED
   External frontend health check: PASSED
   ```

## Next Steps After Fix

Once the Nginx configuration is working:

1. Test all API endpoints from the frontend
2. Verify file uploads work
3. Check document processing functionality
4. Monitor Nginx access logs for any errors
5. Set up monitoring/alerts for the new domain
6. Update any documentation that references the old domain

## Contact

If you encounter issues not covered in this guide, check:
- Nginx error logs: `/var/log/nginx/siufu.api.error.log`
- Backend logs: `docker compose -f docker-compose.prod.yml logs backend`
- Deployment logs: `~/logai-production/deployment.log`
