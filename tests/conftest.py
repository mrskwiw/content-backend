"""
Top-level test configuration.

This file must be at the top level of the tests/ directory to allow
pytest_plugins to work correctly.
"""

# Import fixtures from tests/fixtures/
pytest_plugins = [
    "tests.fixtures.anthropic_responses",
]
