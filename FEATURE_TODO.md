# TODO - Feature Enhancements & Technical Improvements

**Project:** 30-Day Content Jumpstart
**Created:** March 1, 2026
**Purpose:** Track feature enhancements and technical improvements

---

## Database & Infrastructure

### 🔧 Intelligent Database Restore (High Priority)

**Status:** 📋 Planned
**Priority:** High
**Category:** Database/Infrastructure
**Estimated Effort:** 3-4 hours

#### Problem
Current database restore replaces the entire database structure, which breaks when restoring old backups into a codebase with newer schema versions.

#### Proposed Solution
Implement intelligent restore that:
- ✅ Keeps the new database format/schema
- ✅ Intelligently maps backed-up data into new structure
- ✅ Handles missing columns gracefully (uses defaults)
- ✅ Handles new columns (skips data that doesn't exist in backup)
- ✅ Validates data types and constraints before insertion
- ✅ Provides detailed migration report showing what was/wasn't restored

#### Implementation Approach
1. **Schema Comparison**: Compare backup schema with current schema
2. **Column Mapping**: Create mapping of old columns → new columns
3. **Data Transformation**: Transform old data to fit new constraints
4. **Validation**: Validate all data before committing
5. **Reporting**: Generate detailed report of restore process

#### Benefits
- Forward compatibility: Old backups work with new database versions
- Safer restores: Doesn't destroy new schema
- Better migrations: Handles schema evolution gracefully
- Production ready: Safe to use in production environments

#### Files to Modify
- `backend/routers/database.py` (restore endpoint)
- `backend/services/database_service.py` (restore logic)
- New: `backend/services/schema_migration.py` (schema comparison/mapping)

#### Testing
- Unit tests for schema comparison
- Integration tests for various backup versions
- Test with deliberately old backup schema
- Test with missing columns
- Test with new columns

---

## Legend
- 📋 Planned - Not started
- 🔨 In Progress - Currently being worked on
- ✅ Complete - Finished and tested
- 🚫 Blocked - Waiting on dependencies
- 💡 Idea - Needs more research/planning
