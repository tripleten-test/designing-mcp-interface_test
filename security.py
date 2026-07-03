"""
security.py — Input validation for repository and file paths.

Two public functions:

    validate_repo_path(repo_path)
        Raises ValueError if repo_path is not inside any path listed in
        config/allowed_repos.json.  Error message contains "not inside any allowed".

    validate_file_path(repo_path, file_path)
        Raises ValueError if file_path escapes repo_path via directory
        traversal (e.g. "../../etc/passwd").  Error message contains "traversal".
        Returns os.path.join(repo_path, file_path) for safe paths, so that:
            validate_file_path("repo", "src/main.py") == "repo/src/main.py"
"""

from __future__ import annotations

import json
import os
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / "config" / "allowed_repos.json"


def _load_allowed_repos() -> list[str]:
    with open(_CONFIG_PATH) as fh:
        data = json.load(fh)
    return data.get("allowed_repos", [])


def validate_repo_path(repo_path: str) -> str:
    """
    Ensure repo_path is inside at least one entry in allowed_repos.json.

    Raises:
        ValueError: with the phrase "not inside any allowed" when the path
                    is not permitted.

    Returns:
        The original repo_path string unchanged.
    """
    allowed = _load_allowed_repos()
    resolved = Path(repo_path).resolve()

    for entry in allowed:
        entry_resolved = Path(entry).resolve()
        if resolved == entry_resolved or str(resolved).startswith(
            str(entry_resolved) + os.sep
        ):
            return repo_path

    raise ValueError(
        f"'{repo_path}' is not inside any allowed repository. "
        f"Add it to config/allowed_repos.json to permit access."
    )


def validate_file_path(repo_path: str, file_path: str) -> str:
    """
    Ensure file_path does not escape repo_path via directory traversal.

    Raises:
        ValueError: with the phrase "traversal" when the resolved joined path
                    escapes the repo root.

    Returns:
        os.path.join(repo_path, file_path) — the non-resolved joined path —
        so that validate_file_path("repo", "src/main.py") == "repo/src/main.py".
    """
    joined = os.path.join(repo_path, file_path)
    base_resolved = Path(repo_path).resolve()
    joined_resolved = Path(joined).resolve()

    if not str(joined_resolved).startswith(str(base_resolved) + os.sep) and (
        joined_resolved != base_resolved
    ):
        raise ValueError(
            f"Path traversal detected: '{file_path}' escapes the repository "
            f"root '{repo_path}'."
        )

    return joined
