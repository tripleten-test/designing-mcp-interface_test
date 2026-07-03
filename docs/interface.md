We are building a git activity analyzer server 
- Commit patterns 
- Hotspots
- Build history 
- Team structure 

# 1. Questions. 

Which files are risky to change?
  → min data: file change frequency (commit count per file), number of unique authors per file, recency of last change

What's the repository's ownership schema?
  → min data: CODEOWNERS file or equivalent, author-to-file contribution mapping (files touched per author)

What changed most in the last 30 days?
  → min data: commit timestamps, list of files modified per commit (within the date range)

Who made the most commits?
  → min data: commit author (name or email), commit timestamp (to scope to a time range)

Who made the most code reviews?
  → min data: pull request review events (reviewer identity, review timestamp, PR id)


# 2. Identify data sources 

## 2a. Git Commit Logs
- Source: local `.git/` directory via GitPython (`repo.iter_commits()`)
- Fields: commit SHA, author name, author email, timestamp, commit message, list of changed files, lines added/deleted per file
- Sensitive fields: author email → expose as `<author@example.com>` placeholder or hash in responses
- Example record:
  ```
  sha:       "a1b2c3d"
  author:    "Jane Smith"
  email:     "<redacted>"
  timestamp: "2026-04-01T14:32:00Z"
  message:   "fix: resolve null pointer in payment service"
  files:     ["src/payment/handler.ts", "tests/payment.test.ts"]
  additions: 12
  deletions: 4
  ```

## 2b. File Change History
- Source: local `.git/` via GitPython (`git log --follow --name-only`)
- Fields: file path, total commit count, first seen timestamp, last modified timestamp, unique author count
- Derived metric: churn score = commit_count × author_spread (used by `analyze_hotspot`)
- Example record:
  ```
  path:          "src/payment/handler.ts"
  commit_count:  47
  unique_authors: 6
  first_seen:    "2024-11-03T09:00:00Z"
  last_modified: "2026-04-18T11:22:00Z"
  churn_score:   282
  ```

## 2c. Author Contributions
- Source: local `.git/` via GitPython (`git shortlog -sne`)
- Fields: author name, author email, total commits, total lines added, total lines deleted, list of files touched
- Sensitive fields: email → redact or alias as `dev-<id>@org.internal`
- Example record:
  ```
  author:       "Jane Smith"
  email:        "<redacted>"
  commits:      134
  lines_added:  4021
  lines_deleted: 1873
  files_touched: ["src/payment/handler.ts", "src/auth/middleware.ts", ...]
  ```

## 2d. CI/CD Build History
- Source: external API — GitHub Actions (`GET /repos/{owner}/{repo}/actions/runs`) or GitLab CI (`GET /projects/{id}/pipelines`)
- Auth: `GITHUB_TOKEN` or `GITLAB_TOKEN` env var (never logged or returned to client)
- Fields: pipeline id, trigger commit SHA, branch, status (success/failure/cancelled), duration, stage breakdown
- Example record:
  ```
  pipeline_id:   "run-8821"
  commit_sha:    "a1b2c3d"
  branch:        "main"
  status:        "failure"
  duration_secs: 142
  failed_stage:  "test"
  triggered_at:  "2026-04-18T11:25:00Z"
  ```

## 2e. Team Structure
- Source: external API — GitHub (`GET /orgs/{org}/teams/{team}/members`) or internal HR/identity system
- Auth: `ORG_API_TOKEN` env var
- Fields: member login, display name, team name, role (maintainer / member)
- Sensitive fields: personal emails, employee IDs → omit entirely from MCP responses
- Example record:
  ```
  login:   "jsmith"
  name:    "Jane Smith"
  team:    "backend"
  role:    "maintainer"
  ```

## 2f. Repository Ownership
- Source: `CODEOWNERS` file in repo root or `.github/CODEOWNERS` (read directly from `.git` working tree)
- Fields: path pattern, owning team or user handles
- Fallback: derive ownership heuristically from author contribution data if CODEOWNERS is absent
- Example record:
  ```
  pattern: "src/payment/**"
  owners:  ["@org/backend", "@jsmith"]
  ```

## 2g. Deployment History
- Source: external API — GitHub Deployments (`GET /repos/{owner}/{repo}/deployments`), or CI/CD service webhook logs
- Auth: `GITHUB_TOKEN` or `DEPLOY_API_TOKEN` env var
- Fields: deployment id, environment (production/staging/preview), version tag, deployed commit SHA, deployed_at timestamp, status
- Example record:
  ```
  deployment_id: "dep-441"
  environment:   "production"
  version:       "v2.4.1"
  commit_sha:    "a1b2c3d"
  deployed_at:   "2026-04-18T13:00:00Z"
  status:        "success"
  ```

# 3. Map to MCP Primitives 

## Resources (static / slow-changing data, no computation)

### `git-activity://summary/{repo_path}`
- High-level repo stats: total commits, active branches, top contributors, first and last commit date.
- Refreshed on server start or explicit cache bust.

### `git-activity://ownership/{repo_path}`
- Parsed CODEOWNERS entries mapped to path patterns and owner handles.
- Falls back to heuristic author-to-directory mapping when CODEOWNERS is absent.

### `git-activity://team/{org}/{team_slug}`
- Team roster from GitHub Orgs API: member logins, display names, roles (maintainer / member).
- Cached with a configurable TTL (default 15 min).

## Tools (parameterized operations that compute and return results)

### `analyze_hotspot` 
- Inputs: `repo_path`, `branch`, `since`, `until`, `top_n`, `min_commits`, `include_authors`, `path_filter`
- Ranks files by churn score (commit frequency × author spread).
- Returns top-N hotspot files with scores and optional author lists.

### `get_commit_activity`
- Inputs: `repo_path`, `branch`, `since`, `until`, `group_by` (day / week / author)
- Aggregates commit counts over a time range, grouped by the chosen dimension.
- Useful for spotting quiet periods, crunch cycles, or single-author bottlenecks.

## Prompts (guided workflows that orchestrate multiple tools and resources)

### `repo_health_review`
Walks the model through a structured repository health check by chaining resources and tools in order:

```
Step 1 — fetch repo summary
  resource: git-activity://summary/{repo_path}
  → establishes baseline: total commits, contributors, date range

Step 2 — identify recent hotspots
  tool: analyze_hotspot
  inputs: { repo_path, since: "<30 days ago>", top_n: 10, include_authors: true }
  → surfaces the riskiest files to change right now

Step 3 — check commit activity trends
  tool: get_commit_activity
  inputs: { repo_path, since: "<90 days ago>", group_by: "week" }
  → reveals slowdowns, crunch periods, or contributor dropoff

Step 4 — correlate ownership
  resource: git-activity://ownership/{repo_path}
  → maps each hotspot file to its responsible owner or team

Step 5 — synthesize findings
  → produce a written report: top risk files, who owns them,
     recent activity trends, and recommended actions
```

# 4. Design Resource URIs
- git-activity://teams/backend
- git-activity://ownership/CODEOWNERS
- git-activity://summary/{repo_path}

# 5. Design Tool Schemas

---

## Tool 1: `analyze_hotspots`

**Signature:** `analyze_hotspots(repo_path, days=30, branch=...)`

**Returns:** non-empty list of hotspot records, each containing:
- `file` — file path
- `authors` — list of authors who changed the file
- `changes` — number of changes
- `risk_score` — integer risk score

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "analyze_hotspots",
  "description": "Identifies high-churn, high-risk files in a Git repository by analyzing commit frequency, author spread, and recency of changes over a rolling time window.",
  "type": "object",
  "properties": {
    "repo_path": {
      "type": "string",
      "description": "Absolute path to the local Git repository to analyze (e.g. '/home/dev/projects/my-app')."
    },
    "days": {
      "type": "integer",
      "description": "Number of days to look back from today when building the commit history window.",
      "default": 30,
      "minimum": 1,
      "maximum": 365
    },
    "branch": {
      "type": "string",
      "description": "Branch to analyze. Defaults to the repository's default branch (e.g. 'main' or 'master').",
      "default": "main"
    },
    "top_n": {
      "type": "integer",
      "description": "Maximum number of hotspot records to return, ranked by risk_score descending.",
      "default": 10,
      "minimum": 1,
      "maximum": 100
    },
    "min_changes": {
      "type": "integer",
      "description": "Minimum number of changes a file must have within the window to appear in results.",
      "default": 3,
      "minimum": 1
    },
    "path_filter": {
      "type": "string",
      "description": "Optional glob pattern to restrict analysis to a file subtree (e.g. 'src/**/*.ts')."
    }
  },
  "required": ["repo_path"],
  "additionalProperties": false,
  "examples": [
    {
      "title": "Default: last 30 days on main",
      "value": {
        "repo_path": "/home/dev/projects/my-app",
        "days": 30,
        "branch": "main",
        "top_n": 10
      }
    },
    {
      "title": "TypeScript hotspots on develop, last 14 days",
      "value": {
        "repo_path": "/home/dev/projects/my-app",
        "days": 14,
        "branch": "develop",
        "path_filter": "src/**/*.ts",
        "top_n": 5
      }
    }
  ]
}
```

**Response shape:**
```json
[
  {
    "file": "src/payment/handler.ts",
    "authors": ["jane@example.com", "carlos@example.com"],
    "changes": 47,
    "risk_score": 92
  },
  {
    "file": "src/auth/middleware.ts",
    "authors": ["jane@example.com"],
    "changes": 31,
    "risk_score": 74
  }
]
```

---

## Tool 2: `analyze_commit_patterns`

**Signature:** `analyze_commit_patterns(repo_path, days=30, author=...)`

**Returns:** object with aggregate commit pattern data, including:
- `total_commits` — total number of commits in the window
- `avg_files_per_commit` — average number of files touched per commit
- `authors` — per-author breakdown

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "analyze_commit_patterns",
  "description": "Aggregates commit activity in a Git repository over a rolling time window, with optional per-author filtering. Returns summary statistics useful for identifying contributor patterns, crunch periods, and single-author bottlenecks.",
  "type": "object",
  "properties": {
    "repo_path": {
      "type": "string",
      "description": "Absolute path to the local Git repository to analyze (e.g. '/home/dev/projects/my-app')."
    },
    "days": {
      "type": "integer",
      "description": "Number of days to look back from today when scanning commit history.",
      "default": 30,
      "minimum": 1,
      "maximum": 365
    },
    "author": {
      "type": "string",
      "description": "Optional. Filter commits to a single author by name or email substring (e.g. 'jane' or 'jane@example.com'). When omitted, all authors are included."
    },
    "branch": {
      "type": "string",
      "description": "Branch to analyze. Defaults to the repository's default branch.",
      "default": "main"
    },
    "group_by": {
      "type": "string",
      "description": "Dimension to group time-series breakdown by.",
      "enum": ["day", "week", "author"],
      "default": "week"
    }
  },
  "required": ["repo_path"],
  "additionalProperties": false,
  "examples": [
    {
      "title": "Team-wide patterns over the last 30 days",
      "value": {
        "repo_path": "/home/dev/projects/my-app",
        "days": 30,
        "group_by": "week"
      }
    },
    {
      "title": "Single author deep-dive over 90 days",
      "value": {
        "repo_path": "/home/dev/projects/my-app",
        "days": 90,
        "author": "jane@example.com",
        "group_by": "day"
      }
    }
  ]
}
```

**Response shape:**
```json
{
  "total_commits": 134,
  "avg_files_per_commit": 3.2,
  "authors": [
    {
      "name": "Jane Smith",
      "email": "jane@example.com",
      "commits": 87,
      "avg_files_per_commit": 2.9
    },
    {
      "name": "Carlos Rivera",
      "email": "carlos@example.com",
      "commits": 47,
      "avg_files_per_commit": 3.7
    }
  ]
}
```


# 6. Prompt templates (stub)
Repo Health Review: Check build failures, identify the comments that caused them, and reference code hotspots to suggest their attention is needed. check build failures → identify responsible commits → cross-reference hotspots → flag areas needing attention.

# 7. Auth + Security (stub)

Commit logs, file change history, branch info: 	Local git directory
Author contributions, CI/CD history: GitHub / GitLab API
Team structure, repo ownership: External APIs
Deployment history, versions, timestamps: CI/CD or deployment services
