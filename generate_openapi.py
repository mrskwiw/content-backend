"""Generate clean OpenAPI schema without debug output"""
import sys
import os
import logging

# Suppress all logging
logging.disable(logging.CRITICAL)

# Suppress stdout/stderr temporarily
devnull = open(os.devnull, 'w')
old_stdout = sys.stdout
old_stderr = sys.stderr
sys.stdout = devnull
sys.stderr = devnull

try:
    from backend.main import app
finally:
    # Restore stdout/stderr
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    devnull.close()

# Now print the clean JSON
import json
print(json.dumps(app.openapi(), indent=2))
