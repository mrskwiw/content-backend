# Testing Environment Deployment Guide

## Latest Changes (Testing Branch)

**Branch:** `testing` (commit: 800ce41)

**Security Fixes Included:**
- ✅ TR-001: Secure JWT Secret Keys ($45k/year ALE)
- ✅ TR-005: LLM Prompt Injection Defenses ($36k/year ALE)
- ✅ TR-003: Per-User Rate Limiting ($24k/year ALE)
- ✅ TR-008: MFA for Admin Accounts ($18.75k/year ALE)
- ✅ TR-011: HTTPS & HSTS Headers ($3k/year ALE)
- ✅ TR-013: Strong Password Policy ($3k/year ALE)
- ✅ Frontend compatibility fix (X-Frame-Options)

**Total ALE Prevented:** $129,750/year

---

## Deployment Steps

### 1. Pull Latest Changes on Testing Server

```bash
# SSH into testing server
ssh user@testing-server

# Navigate to project
cd /path/to/content-jumpstart

# Pull testing branch
git fetch origin
git checkout testing
git pull origin testing
```

### 2. Update Environment Variables

Ensure these new variables are set in your `.env` file:

```bash
# New dependencies for security features
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# Existing variables (verify they exist)
SECRET_KEY=<generated-secret-32-chars-minimum>
ANTHROPIC_API_KEY=sk-ant-xxx
POSTGRES_PASSWORD=<strong-password-16-chars>
DEFAULT_USER_PASSWORD=<strong-admin-password-12-chars>
```

**Generate new SECRET_KEY:**
```bash
python backend/generate_secret_key.py
```

### 3. Install New Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# New packages added:
# - redis==5.0.1 (for rate limiting)
# - pyotp==2.9.0 (for MFA)
# - qrcode[pil]==7.4.2 (for MFA QR codes)
```

### 4. Database Migration

```bash
# The User model has new MFA fields that need to be added
# Run Alembic migration (if using Alembic):
alembic upgrade head

# OR manually add columns to users table:
# - mfa_enabled (BOOLEAN, default: false)
# - mfa_secret (VARCHAR, nullable)
# - mfa_backup_codes (TEXT, nullable)
# - mfa_enforced (BOOLEAN, default: false)
```

### 5. Start/Restart Services

**Option A: Docker Deployment**
```bash
# Stop current containers
docker-compose down

# Rebuild with latest code
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f api
```

**Option B: Direct Python Deployment**
```bash
# Stop current backend
pkill -f "uvicorn backend.main:app"

# Start backend with new code
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Option C: Systemd Service**
```bash
# Restart service
sudo systemctl restart content-jumpstart
sudo systemctl status content-jumpstart
```

### 6. Verify Deployment

**Check API Health:**
```bash
curl http://testing-server:8000/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-03-20T..."
}
```

**Check Security Headers:**
```bash
curl -I http://testing-server:8000/api/health
```

**Should see:**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

**Test Frontend:**
- Navigate to: http://testing-server:8000
- Should see login page (no blank screen)
- Check browser console for errors

### 7. Test New Features

**Test MFA Enrollment:**
```bash
# POST /api/mfa/enroll (requires auth)
curl -X POST http://testing-server:8000/api/mfa/enroll \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

**Test Rate Limiting:**
```bash
# Make 6 research tool calls rapidly (should get 429 on 6th)
for i in {1..6}; do
  curl -X POST http://testing-server:8000/api/research/run \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -d '{"tool_name": "voice_analysis", ...}'
  sleep 1
done
```

**Test Password Policy:**
```bash
# Try weak password (should fail)
curl -X POST http://testing-server:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "weak",
    "full_name": "Test User"
  }'

# Should return 400 with password requirements
```

---

## Rollback Plan

If issues arise, rollback to previous version:

```bash
# Find previous commit
git log --oneline -10

# Rollback to before security fixes (commit before b456866)
git checkout <previous-commit-hash>

# Restart services
docker-compose down && docker-compose up -d
# OR
sudo systemctl restart content-jumpstart
```

---

## Environment-Specific Notes

**Redis Requirement:**
- Rate limiting now uses Redis for persistence
- Install Redis if not present: `sudo apt-get install redis-server`
- Or use in-memory fallback (automatic if Redis unavailable)

**Database Schema:**
- User table has new MFA columns
- No existing data affected (nullable columns)

**Performance:**
- New middleware adds ~2-5ms per request
- MFA adds ~50ms to login flow
- Rate limiting adds ~1ms per request

---

## Support

If deployment issues occur:
1. Check logs: `docker-compose logs -f` or `journalctl -u content-jumpstart -f`
2. Verify environment variables: `printenv | grep -E 'SECRET_KEY|REDIS|ANTHROPIC'`
3. Test database connection
4. Check Redis connectivity: `redis-cli ping`

**Common Issues:**
- **Blank screen:** Clear browser cache, hard refresh (Ctrl+Shift+R)
- **429 errors:** Redis not connected (using in-memory fallback - limits per instance)
- **500 on startup:** Missing SECRET_KEY or ANTHROPIC_API_KEY
- **MFA not working:** Check system time sync (TOTP requires accurate time)
