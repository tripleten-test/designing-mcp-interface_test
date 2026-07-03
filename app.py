"""
app.py — MCP server initialisation, resource handlers, and prompt template.

All tool registrations live in tools.py (which imports `server` from here).
Run the server via server.py.

# TODO: SSE auth — implement one of the following before deploying over SSE:
#
#   1. JWT verification — decode and verify a Bearer token from the
#      Authorization header using python-jose or PyJWT; reject requests
#      whose signature or expiry is invalid.
#
#   2. API key — accept a static or rotating key via the X-API-Key header;
#      compare against a hashed value stored in an env var (API_KEY_HASH)
#      rather than a plaintext secret.
#
#   3. OAuth 2.0 / OIDC — validate tokens issued by an identity provider
#      (e.g. Auth0, Okta) using their JWKS endpoint; check `aud` and `iss`
#      claims.
#
#   FastMCP does not yet expose per-request middleware natively; add a
#   Starlette middleware layer or upgrade to an MCP version that supports
#   on_connect hooks to enforce auth at the transport boundary.
"""

import json
from mcp.server.fastmcp import FastMCP
from mock_git_utils import MOCK_CODEOWNERS, MOCK_REPO_SUMMARY, MOCK_TEAMS

server = FastMCP("git-activity-analyzer")


# ── Resources ────────────────────────────────────────────────────────────────
# Resources expose static or slow-changing data without requiring computation.
# Dynamic per-repo data is handled by the tools (analyze_hotspots, etc.).


@server.resource("git-activity://summary/{repo_path}")
def get_repo_summary(repo_path: str) -> str:
    """High-level repository stats: total commits, contributors, date range."""
    payload = {**MOCK_REPO_SUMMARY, "repo_path": repo_path}
    return json.dumps(payload, indent=2)


@server.resource("git-activity://teams/backend")
def get_backend_team() -> str:
    """Backend team roster: member logins, display names, roles."""
    return json.dumps(MOCK_TEAMS, indent=2)


@server.resource("git-activity://ownership/CODEOWNERS")
def get_codeowners() -> str:
    """Parsed CODEOWNERS entries: path patterns mapped to owner handles."""
    return json.dumps(MOCK_CODEOWNERS, indent=2)


# ── Prompt ───────────────────────────────────────────────────────────────────


@server.prompt("repo_health_review")
def repo_health_review(repo_path: str) -> str:
    """
    Guided repository health-check workflow.

    Orchestrates the summary resource, hotspot tool, commit-pattern tool, and
    ownership resource in sequence, then synthesises a written report.
    """
    return f"""You are a senior engineering analyst reviewing the health of the
repository at: {repo_path}

Follow these steps in order and do not skip any:

Step 1 — Fetch the repository summary
  Read resource: git-activity://summary/{repo_path}
  Goal: establish baseline stats (total commits, contributors, date range).

Step 2 — Identify recent hotspots
  Call tool: analyze_hotspots
  Arguments: {{ "repo_path": "{repo_path}", "days": 30 }}
  Goal: surface the highest-risk files to change right now.

Step 3 — Check commit-activity trends
  Call tool: analyze_commit_patterns
  Arguments: {{ "repo_path": "{repo_path}", "days": 90 }}
  Goal: reveal slowdowns, crunch periods, or single-author bottlenecks.

Step 4 — Correlate ownership
  Read resource: git-activity://ownership/CODEOWNERS
  Goal: map each hotspot file to its responsible owner or team.

Step 5 — Synthesise findings
  Produce a written report that covers:
  - Top risk files and why they are risky
  - Who owns each risk area
  - Recent activity trends (healthy / concerning / declining)
  - Three concrete, prioritised recommendations for the team
"""
