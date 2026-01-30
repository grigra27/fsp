# Quick Start - Fix Your Deployment

## Run This Now

On your server at `/opt/fair-sber-price`, run:

```bash
chmod +x scripts/fix_deployment.sh
bash scripts/fix_deployment.sh
```

This will fix all three issues:
1. ✅ Remove SSL requirement (nginx will work on HTTP)
2. ✅ Fix database permissions (telegram bot will work)
3. ✅ Initialize database (health checks will pass)

## Expected Output

You should see:
- All containers starting successfully
- No more "unable to open database file" errors
- No more SSL certificate errors
- Health checks passing

## Verify It Works

```bash
# Check all containers are running
docker ps

# Test the API
curl http://localhost:8000/api/health/
curl http://localhost:8000/api/current/

# Check logs (should be clean)
docker logs fsp_web --tail 20
docker logs fsp_telegram_bot --tail 20
docker logs fsp_nginx --tail 20
```

## Add SSL Later (Optional)

Once everything is working on HTTP, add SSL:

```bash
chmod +x scripts/setup_ssl.sh
sudo bash scripts/setup_ssl.sh
```

This will:
- Install certbot
- Get Let's Encrypt certificate
- Update configuration to use HTTPS
- Restart nginx with SSL

## Files Changed

- `docker-compose.prod.yml` - Removed SSL and fixed permissions
- `nginx.conf.nossl` - New HTTP-only nginx config
- `scripts/fix_deployment.sh` - Automated fix script
- `scripts/setup_ssl.sh` - SSL setup script for later

## Need Help?

See `DEPLOYMENT_FIX.md` for detailed troubleshooting.
