# Optimization Branch Rollback Plan

**Branch:** `optimization/phase-1-critical-fixes`
**Purpose:** Procedures for reverting optimizations if issues arise

## Quick Rollback (Emergency)

If critical issues are discovered in production:

```bash
# 1. Switch back to main branch
git checkout main

# 2. Restart services
# Backend
pkill -f uvicorn
uvicorn backend.main:app --port 8000

# Frontend (if separate)
cd operator-dashboard
npm run build
```

**Downtime:** ~2-3 minutes

## Selective Rollback

If only specific optimizations cause issues, you can selectively revert commits:

### Revert GZip Compression (Phase 4.3)
```bash
git revert ef624c9
git push origin HEAD:main
```

**Impact:** Removes response compression, increases bandwidth usage by 3-4x

### Revert N+1 Query Fixes (Phase 4.1)
```bash
git revert b6711b3
git push origin HEAD:main
```

**Impact:** Increases database queries, may slow down list endpoints

### Revert SSE Infrastructure (Phase 3.3)
```bash
git revert 0c09fae
git push origin HEAD:main
```

**Impact:** Removes streaming endpoints (not yet used in production)

### Revert React.memo Optimizations (Phase 3.2)
```bash
git revert a9b3d1a
git push origin HEAD:main
```

**Impact:** More component re-renders, slightly slower frontend

### Revert Monitoring System (Phase 3.1)
```bash
git revert 1d0b72c
git push origin HEAD:main
```

**Impact:** Loses metrics/observability, no functional change

### Revert Caching (Phase 2.5)
```bash
git revert 2a59127
git push origin HEAD:main
```

**Impact:** Slower repeated requests, more API calls

### Revert Error Standardization (Phase 2.4)
```bash
git revert d97cc81
git push origin HEAD:main
```

**Impact:** Loses request ID tracking, less helpful error messages

### Revert Bundle Optimization (Phase 2.3)
```bash
git revert 36c3e22
git push origin HEAD:main
```

**Impact:** Larger frontend bundle (~6MB instead of ~1.4MB)

### Revert Database Indexes (Phase 2.2)
```bash
git revert 02adb36
git push origin HEAD:main
```

**Impact:** Slower filtered queries, no functional change

## Full Rollback to Pre-Optimization State

If all optimizations need to be removed:

```bash
# Find the commit before optimizations started
git log --oneline | grep -B1 "Phase 1"

# Create a revert branch
git checkout -b revert-optimizations main

# Revert all optimization commits (in reverse order)
git revert ef624c9..HEAD --no-commit
git commit -m "Revert all optimization changes"

# Push and deploy
git push origin revert-optimizations:main
```

**WARNING:** This will lose all optimization benefits. Only use in extreme cases.

## Database Rollback

If database migrations caused issues:

```bash
# Check current migration version
python -c "from backend.migrations.manager import MigrationManager; print(MigrationManager().current_version)"

# Rollback to specific version
python -c "from backend.migrations.manager import MigrationManager; MigrationManager().rollback_to(version=4)"

# Restart backend
uvicorn backend.main:app --port 8000
```

**Note:** Database indexes can be dropped without data loss:

```sql
-- If needed, manually drop indexes
DROP INDEX IF EXISTS ix_projects_user_status;
DROP INDEX IF EXISTS ix_projects_created_at_id;
```

## Configuration Rollback

### Disable Compression
```python
# In backend/main.py, comment out:
# add_compression_middleware(app)
```

### Disable Caching
```python
# In backend routers, remove cache decorators:
# @cached(ttl=300, key_prefix="pricing")
```

### Disable Metrics
```python
# In backend/main.py, comment out:
# app.add_middleware(MetricsMiddleware)
```

## Frontend Rollback

### Revert to Non-Optimized Bundle
```bash
git checkout main -- operator-dashboard/vite.config.ts
cd operator-dashboard
npm run build
```

### Disable React.memo
```bash
# Revert specific component files
git checkout main -- operator-dashboard/src/components/wizard/ConversationMessage.tsx
git checkout main -- operator-dashboard/src/components/ui/CopyButton.tsx
# ... etc for other memoized components

cd operator-dashboard
npm run build
```

## Monitoring During Rollback

1. **Check error rates:**
   ```bash
   curl http://localhost:8000/api/metrics/summary
   ```

2. **Monitor logs:**
   ```bash
   tail -f logs/content_jumpstart.log
   ```

3. **Database connections:**
   ```bash
   # SQLite - check lock files
   ls -la data/*.db*
   ```

4. **Frontend errors:**
   ```bash
   # Check browser console
   # Check Network tab for failed requests
   ```

## Post-Rollback Verification

After rolling back:

1. ✅ Run integration tests: `pytest ../tests/integration/`
2. ✅ Check health endpoint: `curl http://localhost:8000/api/health`
3. ✅ Test critical paths:
   - Login
   - Create project
   - Generate content
   - View deliverables

4. ✅ Verify no data loss:
   ```sql
   SELECT COUNT(*) FROM projects;
   SELECT COUNT(*) FROM posts;
   SELECT COUNT(*) FROM deliverables;
   ```

## Common Issues & Solutions

### Issue: "Module not found" errors
**Solution:** Clear Python cache and reinstall
```bash
find . -type d -name __pycache__ -exec rm -rf {} +
pip install -r requirements.txt --force-reinstall
```

### Issue: Frontend won't build
**Solution:** Clean and rebuild
```bash
cd operator-dashboard
rm -rf node_modules dist
npm install
npm run build
```

### Issue: Database locked
**Solution:** Restart backend, check for stale connections
```bash
pkill -f uvicorn
rm data/*.db-wal data/*.db-shm 2>/dev/null || true
uvicorn backend.main:app --port 8000
```

### Issue: Performance worse after rollback
**Solution:** Clear caches, restart services
```bash
# Python cache
rm -rf backend/__pycache__ backend/**/__pycache__

# Browser cache
# Clear browser cache manually

# Restart all services
pkill -f uvicorn
cd operator-dashboard && npm run dev
uvicorn backend.main:app --port 8000
```

## Prevention for Future Optimizations

1. **Feature flags:** Add config toggles for new optimizations
2. **Gradual rollout:** Enable for subset of users first
3. **A/B testing:** Compare performance metrics
4. **Monitoring:** Set up alerts for error rate increases
5. **Backup:** Database snapshot before major changes

## Communication Plan

If rollback is needed:

1. **Notify team:** "Rolling back optimization branch due to [issue]"
2. **Document issue:** Add to BUGS.md with reproduction steps
3. **Timeline:** Estimate time to investigate and fix
4. **Alternative:** Consider partial rollback instead of full revert

## Success Criteria for Re-Deployment

Before re-deploying optimizations after rollback:

- ✅ Root cause identified and fixed
- ✅ All tests passing
- ✅ Issue reproduced and verified fixed
- ✅ Additional tests added to prevent regression
- ✅ Staged rollout plan in place

## Emergency Contacts

- **Main branch maintainer:** Check git log for contact
- **Database admin:** Check team documentation
- **DevOps:** Check team documentation

## Notes

- Most optimizations are non-breaking and can be reverted independently
- Database indexes can be dropped without affecting functionality
- Frontend optimizations (bundle size, React.memo) have no backend dependencies
- Compression and caching are transparent to clients
- Metrics collection doesn't affect request handling

**Last Updated:** 2026-03-20
