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

## Research Tools

### 🎯 Enhance Content Gap Analysis with Full Client Context (High Priority)

**Status:** 📋 Planned
**Priority:** High
**Category:** Research Tools / AI Prompting
**Estimated Effort:** 2-3 hours

#### Problem
Current content gap tool produces generic analysis that doesn't fully leverage available client information. Analysis lacks business-specific insights and strategic depth.

#### Proposed Solution
Revise content gap tool to:
- ✅ Include ALL client information in context (business description, ideal customer, pain points, questions, tone, existing content topics)
- ✅ Add specific instructions to ensure analysis is tailored to the specific business (not generic)
- ✅ Adopt persona of experienced marketing strategist for deeper strategic insights
- ✅ Reference client's actual pain points and customer questions in gap recommendations
- ✅ Align gap priorities with client's business goals and target audience
- ✅ Provide actionable content recommendations specific to client's industry and tone

#### Implementation Approach
1. **Context Enhancement**: Build comprehensive client context from all available fields
2. **Prompt Revision**: Update system prompt to include marketing strategist persona
3. **Instruction Specificity**: Add explicit instructions to avoid generic recommendations
4. **Data Integration**: Reference client pain points, customer questions, and existing topics in analysis
5. **Quality Validation**: Ensure recommendations mention specific client details

#### Benefits
- More valuable, actionable insights for clients
- Analysis directly addresses client's specific challenges
- Recommendations aligned with business goals and audience
- Higher perceived value of research tools ($500 add-on)
- Better integration with overall content strategy

#### Files to Modify
- `src/research/content_gap_analysis.py` (prompt engineering, context building)
- `src/research/research_context_builder.py` (if exists - for context assembly)
- Potentially `backend/services/research_service.py` (_prepare_inputs method)

#### Example Enhancements
**Before:** "Create how-to content about project management"
**After:** "Create 'How Small Teams (5-20 people) Can Eliminate Email Chaos with Async Project Management' - directly addressing your customer's #1 pain point about scattered communication"

#### Testing
- Test with minimal client data (ensure graceful degradation)
- Test with complete client data (verify all context is used)
- Verify recommendations reference specific client details
- Check for generic vs. specific language in outputs
- Validate strategic depth and actionability

---

## Legend
- 📋 Planned - Not started
- 🔨 In Progress - Currently being worked on
- ✅ Complete - Finished and tested
- 🚫 Blocked - Waiting on dependencies
- 💡 Idea - Needs more research/planning
