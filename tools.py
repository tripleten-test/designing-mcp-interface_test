"""
tools.py — MCP tool registrations for the git-activity-analyzer server.

Imports `server` from app.py (required by spec) and registers the two
parameterised tools.  Security validation runs before any analysis so that
invalid or disallowed repo paths are rejected at the boundary.
"""

from app import server
from analysis import analyze_commit_patterns as _analyze_commit_patterns
from analysis import analyze_hotspots as _analyze_hotspots
from security import validate_repo_path


@server.tool()
def analyze_hotspots(
    repo_path: str,
    days: int = 30,
    branch: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """
    Identify high-churn, high-risk files in a Git repository.

    Args:
        repo_path: Absolute path to the local git repository.
        days:      Look-back window in days (default 30).
        branch:    Branch to analyse; defaults to the repo's default branch.
        limit:     Maximum number of hotspot records to return.

    Returns:
        Non-empty list of hotspot records, each with:
          file, authors, changes, risk_score (int).
    """
    validate_repo_path(repo_path)
    return _analyze_hotspots(repo_path, days=days, branch=branch, limit=limit)


@server.tool()
def analyze_commit_patterns(
    repo_path: str,
    days: int = 30,
    author: str | None = None,
) -> dict:
    """
    Aggregate commit-activity statistics over a rolling time window.

    Args:
        repo_path: Absolute path to the local git repository.
        days:      Look-back window in days (default 30).
        author:    Optional author name/email substring to filter commits.

    Returns:
        Dict with total_commits, avg_files_per_commit, and authors list.
    """
    validate_repo_path(repo_path)
    return _analyze_commit_patterns(repo_path, days=days, author=author)
