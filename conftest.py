"""
conftest.py — Pytest root configuration.

Inserts the project root into sys.path so that modules such as `security`,
`analysis`, and `git_utils` can be imported regardless of which directory
pytest is invoked from (e.g. running `pytest` from /tests in CI).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
