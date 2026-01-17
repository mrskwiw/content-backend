# Test Coverage Plan: Achieving 90% Coverage

## Current Status
**Date:** 2026-01-13
**Current Coverage:** 65.04% (5,366/7,915 lines)
**Target Coverage:** 90% (7,124/7,915 lines)
**Gap:** 1,758 lines need coverage
**Test Results:** 1,106 passed, 26 failed, 13 skipped

## Strategy Overview

To reach 90% coverage, we need to:
1. Fix 26 failing unit tests
2. Add tests for 14 files with 0% coverage (1,419 lines)
3. Improve 6 files with <50% coverage (638 lines)
4. Improve 4 files with 50-70% coverage (343 lines)

Total improvement needed: ~2,400 lines to reach 7,124 covered lines

## Priority 1: Fix Failing Tests (26 failures)

### Mock Object Issues
**Files:** test_analytics_tracker.py, test_template_quantities_generation.py
**Issue:** Mock objects being treated as strings in validators
**Fix:**
- Update mocks to return string values instead of Mock objects
- Configure Mock.spec or Mock.return_value properly
- Add `.return_value = "string"` to content mocks

**Affected Tests:**
- `test_create_csv_includes_cta_status` - Analytics tracker CTA detection
- `test_generate_posts_async_with_quantities` - Template quantities generation
- `test_generate_posts_async_concurrency` - Async concurrency testing
- `test_generate_posts_async_priority` - Template priority

### Pydantic ValidationError Issues
**Files:** test_coordinator.py, test_brief_parser.py
**Issue:** Pydantic validation failing on enum conversions
**Fix:**
- Update test data to match current Pydantic v2 schema
- Add proper enum value mapping
- Handle missing/optional fields correctly

**Affected Tests:**
- `test_convert_brand_personality_to_enum` - BrandPersonality enum
- `test_convert_data_usage_enum` - Data usage preferences
- `test_analyze_voice_samples` - Voice sample validation

### File Path Issues
**Files:** test_output_formatter.py, test_file_parser.py
**Issue:** Windows path separators causing file not found errors
**Fix:**
- Use `pathlib.Path` for cross-platform paths
- Mock file system operations in tests
- Use temporary directories (`tmp_path` fixture)

**Affected Tests:**
- `test_init_with_default_dir` - Output formatter initialization
- `test_extract_from_docx_success` - DOCX file parsing

### Research Tool Issues
**Files:** test_research_tool_mapping.py
**Issue:** Research tools recently refactored/removed
**Fix:**
- Update test to match current tool structure
- Remove references to deprecated tools
- Verify tool mapping against actual implementation

## Priority 2: Add Tests for 0% Coverage Files (14 files, 1,419 lines)

### High Impact Files (>100 lines each)

#### 1. src/cli/interactive_mode.py (278 lines, 0% coverage)
**Module:** CLI interactive brief builder
**Tests Needed:**
- Test question prompts and user input flow
- Test brief assembly from user responses
- Test validation of interactive inputs
- Test file save operations
**Estimated Tests:** 15-20 tests
**File:** `tests/unit/cli/test_interactive_mode.py`

#### 2. src/utils/cost_dashboard.py (146 lines, 0% coverage)
**Module:** Cost tracking dashboard utilities
**Tests Needed:**
- Test cost calculation by tier
- Test dashboard data aggregation
- Test budget alerts and warnings
- Test cost reporting formats
**Estimated Tests:** 10-12 tests
**File:** `tests/unit/test_cost_dashboard.py` (update existing)

#### 3. src/config/secrets_manager.py (137 lines, 0% coverage)
**Module:** Secrets/API key management
**Tests Needed:**
- Test secret loading from environment
- Test secret validation
- Test fallback mechanisms
- Mock environment variables
**Estimated Tests:** 8-10 tests
**File:** `tests/unit/test_secrets_manager.py`

#### 4. src/agents/brief_quality_checker.py (122 lines, 0% coverage)
**Module:** Brief completeness and quality validation
**Tests Needed:**
- Test required field validation
- Test quality score calculation
- Test improvement suggestions
- Test edge cases (empty/partial briefs)
**Estimated Tests:** 12-15 tests
**File:** `tests/unit/agents/test_brief_quality_checker.py`

#### 5. src/utils/progress_stream.py (121 lines, 0% coverage)
**Module:** Real-time progress streaming
**Tests Needed:**
- Test progress event emission
- Test stream buffering
- Test completion callbacks
- Mock async streams
**Estimated Tests:** 8-10 tests
**File:** `tests/unit/test_progress_stream.py`

#### 6. src/agents/brief_enhancer.py (95 lines, 0% coverage)
**Module:** AI-powered brief enhancement
**Tests Needed:**
- Test enhancement suggestions
- Test missing field detection
- Test API integration (mocked)
- Test enhancement quality
**Estimated Tests:** 10-12 tests
**File:** `tests/unit/agents/test_brief_enhancer.py`

#### 7. src/agents/keyword_agent.py (96 lines, 0% coverage)
**Module:** SEO keyword extraction and strategy
**Tests Needed:**
- Test keyword extraction from brief
- Test keyword scoring/ranking
- Test keyword grouping
- Test API integration (mocked)
**Estimated Tests:** 10-12 tests
**File:** `tests/unit/agents/test_keyword_agent.py`

### Medium Impact Files (50-100 lines each)

#### 8. src/database/migrate_phase8b.py (78 lines, 0% coverage)
**Module:** Database migration script
**Tests Needed:**
- Test migration execution
- Test rollback functionality
- Test idempotency
- Mock database operations
**Estimated Tests:** 6-8 tests
**File:** `tests/unit/database/test_migrate_phase8b.py`

#### 9. src/agents/question_generator.py (77 lines, 0% coverage)
**Module:** Generates discovery questions
**Tests Needed:**
- Test question generation
- Test question prioritization
- Test API integration (mocked)
**Estimated Tests:** 8-10 tests
**File:** `tests/unit/agents/test_question_generator.py`

#### 10. src/agents/keyword_refiner.py (64 lines, 0% coverage)
**Module:** Refines and optimizes keyword lists
**Tests Needed:**
- Test keyword deduplication
- Test relevance filtering
- Test optimization suggestions
**Estimated Tests:** 6-8 tests
**File:** `tests/unit/agents/test_keyword_refiner.py`

### Low Impact Files (<50 lines each)

#### 11. src/models/brief_quality.py (31 lines, 0% coverage)
**Module:** Brief quality score model
**Tests Needed:**
- Test model creation and validation
- Test score calculation
- Test quality thresholds
**Estimated Tests:** 4-6 tests
**File:** `tests/unit/models/test_brief_quality.py`

#### 12-14. Config backup files (58 lines combined, 0% coverage)
- `template_rules_expanded.py` (23 lines)
- `template_rules_original_backup.py` (11 lines)
- `models/question.py` (23 lines)

**Decision:** **Exclude from coverage** - These are backup/deprecated files.
**Action:** Add to `.coveragerc` exclusion list

## Priority 3: Improve Low Coverage Files (<50%, 6 files)

### 1. src/validators/research_input_validator.py (9% coverage, 113/132 uncovered)
**Current:** 9% (19/132 lines)
**Target:** 90% (119/132 lines)
**Gap:** 100 lines
**Tests Needed:**
- Input sanitization tests
- Validation rule tests
- Error message tests
- Edge case validation
**Estimated Tests:** 15-20 tests
**File:** `tests/unit/validators/test_research_input_validator.py`

### 2. src/config/platform_specs.py (35% coverage, 17/31 uncovered)
**Current:** 35%
**Target:** 90%
**Gap:** 17 lines
**Tests Needed:**
- Platform spec retrieval tests
- Spec validation tests
- Default value tests
**Estimated Tests:** 8-10 tests
**File:** `tests/unit/test_platform_specs.py`

### 3. src/database/project_db.py (39% coverage, 260/444 uncovered)
**Current:** 39% (184/444 lines)
**Target:** 90% (400/444 lines)
**Gap:** 216 lines
**Tests Needed:**
- CRUD operation tests
- Query tests
- Transaction tests
- Error handling tests
- Relationship tests
**Estimated Tests:** 30-40 tests
**File:** `tests/unit/database/test_project_db.py` (expand existing)

### 4. src/config/brand_frameworks.py (48% coverage, 15/34 uncovered)
**Current:** 48%
**Target:** 90%
**Gap:** 15 lines
**Tests Needed:**
- Brand archetype mapping tests
- Framework selection tests
- Personality trait tests
**Estimated Tests:** 8-10 tests
**File:** `tests/unit/test_brand_frameworks.py`

### 5. src/utils/enhanced_response_cache.py (52% coverage, 70/169 uncovered)
**Current:** 52% (99/169 lines)
**Target:** 90% (152/169 lines)
**Gap:** 53 lines
**Tests Needed:**
- Cache hit/miss tests
- TTL expiration tests
- Cache invalidation tests
- Memory management tests
**Estimated Tests:** 12-15 tests
**File:** `tests/unit/test_enhanced_response_cache.py` (expand existing)

### 6. src/models/quality_profile.py (53% coverage, 24/54 uncovered)
**Current:** 53% (30/54 lines)
**Target:** 90% (49/54 lines)
**Gap:** 19 lines
**Tests Needed:**
- Profile validation tests
- Threshold calculation tests
- Profile comparison tests
**Estimated Tests:** 10-12 tests
**File:** `tests/unit/models/test_quality_profile.py` (expand existing)

## Priority 4: Improve Medium Coverage Files (50-70%, 4 files)

### 1. src/agents/coordinator.py (59% coverage, 80/225 uncovered)
**Current:** 59% (145/225 lines)
**Target:** 90% (203/225 lines)
**Gap:** 58 lines
**Tests Needed:**
- Workflow coordination tests
- Error handling paths
- Edge case scenarios
**Estimated Tests:** 15-20 tests
**File:** `tests/unit/test_coordinator.py` (fix failing + add new)

### 2. src/models/client_brief.py (64% coverage - currently at 79%)
**Note:** Already above 70%, skip for now

### 3. src/agents/client_classifier.py (68% coverage, 14/44 uncovered)
**Current:** 68% (30/44 lines)
**Target:** 90% (40/44 lines)
**Gap:** 10 lines
**Tests Needed:**
- Classification edge cases
- Confidence threshold tests
- Unknown client type handling
**Estimated Tests:** 6-8 tests
**File:** `tests/unit/test_client_classifier.py` (expand existing)

### 4. src/utils/template_cache.py (69% coverage, 23/86 uncovered)
**Current:** 69% (63/86 lines)
**Target:** 90% (77/86 lines)
**Gap:** 14 lines
**Tests Needed:**
- Cache invalidation
- Template reload
- Error scenarios
**Estimated Tests:** 8-10 tests
**File:** `tests/unit/test_template_cache.py` (expand existing)

### 5. src/validators/hook_validator.py (70% coverage, 34/125 uncovered)
**Current:** 70% (91/125 lines)
**Target:** 90% (113/125 lines)
**Gap:** 22 lines
**Tests Needed:**
- Platform-specific hook validation
- Edge case hooks
- Similarity threshold testing
**Estimated Tests:** 10-12 tests
**File:** `tests/unit/test_hook_validator.py` (expand existing)

## Implementation Plan

### Phase 1: Fix Failing Tests (Days 1-2)
**Target:** 0 failures, 90% pass rate on existing tests
**Tasks:**
1. Fix mock object issues in analytics and template tests
2. Fix Pydantic validation in coordinator and brief parser
3. Fix file path issues in output formatter and file parser
4. Update research tool mapping tests

**Success Criteria:** All 1,132 tests passing

### Phase 2: Add High Impact Tests (Days 3-5)
**Target:** +400 lines covered
**Tasks:**
1. Add tests for interactive_mode.py (278 lines)
2. Add tests for cost_dashboard.py (146 lines)
3. Add tests for secrets_manager.py (137 lines)
4. Add tests for brief_quality_checker.py (122 lines)
5. Add tests for progress_stream.py (121 lines)

**Success Criteria:** Coverage increases to ~72%

### Phase 3: Add Medium Impact Tests (Days 6-7)
**Target:** +250 lines covered
**Tasks:**
1. Add tests for brief_enhancer.py (95 lines)
2. Add tests for keyword_agent.py (96 lines)
3. Add tests for migrate_phase8b.py (78 lines)
4. Add tests for question_generator.py (77 lines)
5. Add tests for keyword_refiner.py (64 lines)

**Success Criteria:** Coverage increases to ~78%

### Phase 4: Improve Low Coverage Files (Days 8-10)
**Target:** +400 lines covered
**Tasks:**
1. Improve research_input_validator.py (9% → 90%)
2. Improve project_db.py (39% → 90%)
3. Improve enhanced_response_cache.py (52% → 90%)
4. Improve platform_specs.py (35% → 90%)
5. Improve brand_frameworks.py (48% → 90%)
6. Improve quality_profile.py (53% → 90%)

**Success Criteria:** Coverage increases to ~85%

### Phase 5: Final Push to 90% (Days 11-12)
**Target:** +200 lines covered
**Tasks:**
1. Improve coordinator.py (59% → 90%)
2. Improve hook_validator.py (70% → 90%)
3. Improve template_cache.py (69% → 90%)
4. Improve client_classifier.py (68% → 90%)
5. Add missing edge case tests across all modules

**Success Criteria:** Coverage reaches 90%

### Phase 6: Validation & Documentation (Day 13)
**Tasks:**
1. Run full test suite with coverage
2. Generate HTML coverage report
3. Document remaining uncovered lines (accept <10%)
4. Update test documentation
5. Run type checking and linting

**Success Criteria:**
- Coverage ≥ 90%
- All tests passing
- Clean mypy and ruff checks

## Testing Best Practices

### 1. Mock External Dependencies
- Mock Anthropic API calls using `unittest.mock`
- Mock file system operations using `tmp_path` fixtures
- Mock database operations using in-memory SQLite

### 2. Test Structure
```python
class TestModuleName:
    def test_function_success_case(self):
        """Test successful execution"""
        pass

    def test_function_error_case(self):
        """Test error handling"""
        pass

    def test_function_edge_case(self):
        """Test boundary conditions"""
        pass
```

### 3. Use Fixtures
- Create reusable fixtures in `conftest.py`
- Use `@pytest.fixture` for setup/teardown
- Share fixtures across test modules

### 4. Test Coverage Focus
- Aim for branch coverage, not just line coverage
- Test both success and failure paths
- Test edge cases and boundary conditions
- Test error handling and exceptions

### 5. Keep Tests Fast
- Use mocks instead of real API calls
- Use in-memory databases
- Avoid network I/O in unit tests
- Run integration tests separately

## Coverage Exclusions

Add these to `pyproject.toml` coverage exclusions:
```toml
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__pycache__/*",
    "*/migrations/*",
    "*/.venv/*",
    "*/venv/*",
    "*/backend/*",
    "*/research/*",
    "src/research/*",
    "src/config/template_rules_expanded.py",
    "src/config/template_rules_original_backup.py",
    "src/models/question.py",  # Deprecated
]
```

## Success Metrics

- **Unit Test Coverage:** ≥ 90%
- **Branch Coverage:** ≥ 85%
- **Test Pass Rate:** 100%
- **Test Execution Time:** < 3 minutes for unit tests
- **Code Quality:** Pass mypy strict mode
- **Linting:** Pass ruff with no warnings

## Maintenance

### Ongoing Coverage Monitoring
1. Run coverage with every commit: `pytest --cov=src --cov-fail-under=90`
2. Review coverage reports weekly
3. Add tests for new features before merging
4. Maintain 90% minimum threshold in CI/CD

### Coverage Report Generation
```bash
# Generate HTML report
pytest --cov=src --cov-report=html

# Generate JSON report
pytest --cov=src --cov-report=json

# Generate term report with missing lines
pytest --cov=src --cov-report=term-missing
```

## Estimated Timeline

**Total Effort:** 13 days (assuming 6-8 hours/day)

- **Phase 1:** 2 days (Fix failing tests)
- **Phase 2:** 3 days (High impact tests)
- **Phase 3:** 2 days (Medium impact tests)
- **Phase 4:** 3 days (Low coverage improvements)
- **Phase 5:** 2 days (Final push to 90%)
- **Phase 6:** 1 day (Validation & docs)

**Deliverables:**
- 90%+ test coverage across src/ directory
- All tests passing (1,300+ total tests)
- Comprehensive test documentation
- HTML coverage reports
- Updated testing guidelines

---
**Status:** PLAN CREATED
**Next Step:** Begin Phase 1 - Fix failing tests
**Owner:** Development Team
**Last Updated:** 2026-01-13
