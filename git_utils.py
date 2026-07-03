"""
git_utils.py — Thin wrapper around GitPython for reading commit history.

`open_repo` returns a real GitRepository when the path is a valid git repo,
or a MockGitRepository when it is not (e.g. in tests or demos).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mock_git_utils import MockGitRepository


class GitRepository:
    """Wraps a real git.Repo and exposes the subset of data the tools need."""

    def __init__(self, repo) -> None:
        self._repo = repo

    def get_commits(
        self,
        days: int = 30,
        branch: str | None = None,
        author: str | None = None,
    ) -> list[dict]:
        """
        Return commits from the past `days` days on `branch`.

        Each commit dict mirrors the shape expected by analysis.py:
          {author_email, changed_files, committed_datetime}
        """
        since = datetime.now(timezone.utc) - timedelta(days=days)
        kwargs: dict = {"since": since.isoformat()}
        if branch:
            kwargs["rev"] = branch
        if author:
            kwargs["author"] = author

        commits = []
        for commit in self._repo.iter_commits(**kwargs):
            committed_dt = datetime.fromtimestamp(
                commit.committed_date, tz=timezone.utc
            )
            commits.append(
                {
                    "author_email": commit.author.email,
                    "changed_files": list(commit.stats.files.keys()),
                    "committed_datetime": committed_dt,
                }
            )
        return commits

    def get_changed_files(self, commit: dict) -> list[str]:
        return commit["changed_files"]


class MockRepositoryAdapter:
    """
    Normalises MockGitRepository's MockCommit objects to the same dict shape
    that GitRepository.get_commits() produces, so analysis.py has a single
    interface to work against.
    """

    def __init__(self, mock_repo) -> None:
        self._mock = mock_repo

    def get_commits(
        self,
        days: int = 30,
        branch: str | None = None,  # noqa: ARG002 — mock ignores branch
        author: str | None = None,
    ) -> list[dict]:
        raw = self._mock.get_commits(days)
        result = []
        for commit in raw:
            email = commit.author.email
            if author and author.lower() not in email.lower():
                continue
            result.append(
                {
                    "author_email": email,
                    "changed_files": commit.changed_files,
                    "committed_datetime": commit.committed_datetime,
                }
            )
        return result


def open_repo(repo_path: str) -> GitRepository | MockRepositoryAdapter:
    """
    Open `repo_path` as a real git repository.

    Falls back to a MockRepositoryAdapter (backed by MockGitRepository) when
    the path is not a valid git repo (missing .git, permission error, etc.).
    Both return types expose the same `get_commits(days, branch, author)`
    interface returning list[dict].
    """
    try:
        import git  # type: ignore[import]

        raw = git.Repo(repo_path, search_parent_directories=False)
        return GitRepository(raw)
    except Exception:
        from mock_git_utils import MockGitRepository

        return MockRepositoryAdapter(MockGitRepository(repo_path))
