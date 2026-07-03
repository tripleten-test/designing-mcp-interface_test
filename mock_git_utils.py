"""
Stub for unit tests and demos.
Swap GitRepository for MockGitRepository to work without a real git repo.

TODO: Add adapters for GitHub API, GitLab, Jira, or a database here
      when replacing mock data with real integrations.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MockAuthor:
    email: str


@dataclass
class MockCommit:
    author: MockAuthor
    changed_files: list[str] = field(default_factory=list)
    committed_datetime: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class MockGitRepository:
    def __init__(self, path: str):
        self.path = path
        self._commits = SAMPLE_COMMITS

    def get_commits(self, days: int) -> list[MockCommit]:
        return self._commits

    def get_changed_files(self, commit: MockCommit) -> list[str]:
        return commit.changed_files


SAMPLE_COMMITS = [
    MockCommit(MockAuthor("alice@example.com"), ["src/auth.py", "src/models.py"]),
    MockCommit(MockAuthor("bob@example.com"), ["src/auth.py", "tests/test_auth.py"]),
    MockCommit(MockAuthor("alice@example.com"), ["src/auth.py"]),
    MockCommit(MockAuthor("carol@example.com"), ["src/models.py", "src/api.py"]),
]


# ─── Mock data for Resources ────────────────────────────────────────────────

MOCK_REPO_SUMMARY = {
    "name": "example-repo",
    "default_branch": "main",
    "total_commits": 1234,
    "active_contributors": 8,
    "last_commit_date": "2025-01-15T10:30:00Z",
    "languages": {"Python": 65, "JavaScript": 25, "Shell": 10},
}

MOCK_TEAMS = {
    "team": "backend",
    "members": [
        {"name": "Alice", "email": "alice@example.com", "role": "lead"},
        {"name": "Bob", "email": "bob@example.com", "role": "developer"},
        {"name": "Carol", "email": "carol@example.com", "role": "developer"},
    ],
}

MOCK_CODEOWNERS = {
    "owners": [
        {"pattern": "src/auth/*", "owners": ["@alice", "@security-team"]},
        {"pattern": "src/api/*", "owners": ["@backend-team"]},
        {"pattern": "src/models/*", "owners": ["@alice", "@bob"]},
        {"pattern": "tests/*", "owners": ["@qa-team"]},
    ]
}
