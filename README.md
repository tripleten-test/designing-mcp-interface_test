In this task, you'll design an MCP interface for a Git Activity Analyzer — a server that lets a coding agent query repository info (history, hotspots, CI, ownership) through structured resources and tools.

## Workflow at a glance

👩‍💻
1. Set up your environment
2. Plan the interface in `docs/interface.md`
3. Build the server
(Optional: use a prepared prompt to speed up your first draft)
4. Check your work
5. Submit

## 1. Set up your environment

Once you log in to your GitHub account, the repository for this task will be added automatically.

1. Confirm that `designing-mcp-interface` appears in your account. 
2. Clone the repo locally and open it in your editor (Cursor, VS Code, etc.)

**Prerequisites**:

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/) package manager
- A Git repository to analyze (any public repo works, e.g. https://github.com/facebook/react)

## 2. Interface design

### **2.1. Write down host questions**

1. Create or open `docs/interface.md`.
2. Add 5–8 questions the server should be able to answer.
    
    **Examples:**
    
    - Which files are risky to change?
    - What's the repository's ownership schema?
    - What changed most in the last 30 days?

  3. For each question, specify the minimum required data.

### **2.2. Identify data sources**

In `docs/interface.md`, list the data sources your server will expose. Consider these categories:

- Git commit logs (authors, timestamps, messages, diffs)
- File change history (frequently modified files)
- Author contributions (lines added/deleted, files touched)
- CI/CD build history (runs, stages, pass/fail)
- Team structure (members, roles)
- Repository ownership (code owners, review policies)
- Deployment history (environments, version, timestamp)

<aside>
📌 Your data may come from `.git` (using GitPython or an equivalent library) or external APIs (e.g. GitHub Actions, GitLab CI, internal dashboards). Feel free to use placeholders to avoid exposing sensitive data.
</aside>

### **2.3. Map capabilities to MCP primitives**

In `docs/interface.md`, map each capability to one MCP primitive:

- Resource → static data
- Tool → parameterized operation that computes or returns results
- Prompt → guided workflow (often orchestrates multiple tools)

Include at least:

- 3 resources
- 2 tools
- 1 prompt template

## 3. Build the server

Create a minimal working MCP server that matches your interface design.

### **3.1. Define resource URIs**

1. In the server code, add at least three resources with stable URIs.
2. Use a consistent URI scheme, for example:
    - `git-activity://summary/{repo_path}`
    - `git-activity://teams/backend`
    - `git-activity://ownership/CODEOWNERS`

### **3.2. Implement the tools**

Add the following two tools:

1. `analyze_hotspots(repo_path, days=30, branch=...)`
    
    Returns a non-empty list of hotspot records.
    
    Each record should include:
    
    - `file` — file path
    - `authors` — list of authors who changed the file
    - `changes` — number of changes
    - `risk_score` — integer risk score
2. `analyze_commit_patterns(repo_path, days=30, author=...)`
    
    Returns a dictionary or object with commit pattern data.
    
    It should include:
    
    - `total_commits`
    - `avg_files_per_commit`
    - `authors`

Define JSON input schemas (name, description, parameters) for both tools. Both should include the `repo_path` parameter. 

You can use a simple prompt for that: 

> *Write a JSON Schema for the Git Activity Analyzer tool <tool_name> in the <specific repository>*
> 

## **Extra mile (optional)**

Add an extra tool of your choice.

### **Option 1: Add a prompt template as a workflow**

1. Add at least one prompt template.
2. Design it as a workflow that references one of the mandatory tools (`analyze_hotspots`  or `analyze_commit_patterns`).
    
    <aside>
    👩‍💻
    
    **Example**
    
    Repo health review: check build failures → identify problematic commits → cross-reference hotspots → generate recommendations
    
    </aside>
    

### **Option 2: Add permission boundaries**

1. Implement repository access control:
    - Create a config file `config/allowed_repos.json`
    - Check that `repo_path` is in the allowed directories
    - Check that `file_path` stays inside the repo (block `../` traversal)
2. Add a transport security placeholder (if SSE is used): add a simple auth check (API key or JWT header) or a documented TODO in the SSE middleware.

## **🚀 Speed up with a prompt (optional)**

You can use AI to generate a first implementation of the server. Do this only **after** drafting your interface in `docs/interface.md` and attach it to the prompt.

Then review the code, test it locally, and make sure the final implementation meets all requirements.

#### Prompt

```markdown
You are working on an MCP (Model Context Protocol) server called "git-activity-analyzer".

Build the project to satisfy these exact requirements.

Use my docs/interface.md as the design source of truth.
Implement the server so that the resources, tools, and prompt template align with that interface design.

Project files that must exist:
- app.py
- server.py
- tools.py
- analysis.py
- security.py
- git_utils.py
- mock_git_utils.py
- config/allowed_repos.json
- docs/interface.md
- pyproject.toml

Important implementation constraints:
- app.py must initialize the server with: server = FastMCP("git-activity-analyzer")
- tools.py must contain exactly: from app import server
- analysis.py must define:
  - analyze_hotspots
  - analyze_commit_patterns
- security.py must define:
  - validate_repo_path
  - validate_file_path
- mock_git_utils.py must define:
  - MockGitRepository
  - SAMPLE_COMMITS

Resources to register with stable URIs using the git-activity:// scheme:
- git-activity://summary/{repo_path}
- git-activity://teams/backend
- git-activity://ownership/CODEOWNERS

Required tools:
1. analyze_hotspots(repo_path, days=30, branch=None)
2. analyze_commit_patterns(repo_path, days=30, author=None)

Tool output contracts:
- analyze_hotspots must return a non-empty list
- each list item must contain:
  - file
  - authors
  - changes
  - risk_score
- risk_score must be an integer

- analyze_commit_patterns must return a dict containing:
  - total_commits
  - avg_files_per_commit
  - authors

Mock/test fixture requirements:
- SAMPLE_COMMITS must be set up so analyze_commit_patterns(...) returns total_commits == 4

Security requirements:
- config/allowed_repos.json must contain at least one allowed repo path
- validate_repo_path("/etc/passwd") must raise ValueError
- the error message must contain: "not inside any allowed"
- validate_file_path("/repo", "../../etc/passwd") must raise ValueError
- the error message must contain: "traversal"
- validate_file_path("repo", "src/main.py") must return: repo/src/main.py

Other requirements:
- app.py must use FastMCP
- include authentication implementation or a clear TODO for SSE auth
- pyproject.toml must include gitpython and mcp

Build the simplest implementation that satisfies these requirements. 
```

## 4. Check your work

Before submitting, test your functionality locally and review the submission checklist. 

### ✅ Submission checklist

- [ ]  `docs/interface.md` with at least five questions, listed data sources, and mapped MCP primitives
- [ ]  At least three resources with stable URIs using the `git-activity://...` scheme
- [ ]  At least two tools, including:
    - [ ]  `analyze_hotspots` — returns a non-empty list with `file`, `authors`, `changes`, and `risk_score` (int)
    - [ ]  `analyze_commit_patterns` — returns a dict with `total_commits`, `avg_files_per_commit`, and `authors`
    - [ ]  Both required tools include `repo_path`
- [ ]  At least one prompt template that uses one of the required tools (`analyze_hotspots`  or `analyze_commit_patterns`)

#### Required files and functions

- [ ]  `server.py`
- [ ]  `analysis.py`
- [ ]  `security.py`
- [ ]  `mock_git_utils.py`
- [ ]  `git_utils.py`
- [ ]  `app.py`
- [ ]  `app.py` (uses FastMCP)
- [ ]  `analysis.py` — contains:
    - [ ]  `analyze_hotspots`
    - [ ]  `analyze_commit_patterns`
- [ ]  `security.py` — contains:
    - [ ]  `validate_repo_path`
    - [ ]  `validate_file_path`
- [ ]  `tools.py` imports the server from `app.py` in a way that avoids circular imports

#### Security

- [ ]  `config/allowed_repos.json` exists with ≥ 1 allowed repo path
- [ ]  Python code includes `validate_repo_path` or `allowed_repos` logic
- [ ]  File path traversal protection is implemented: `../`, `"traversal"`, or `validate_file_path`
- [ ]  Authentication is implemented, or a clear TODO is documented: `jwt`, `api key`, `api_key`, or `auth`

#### **Test fixtures**

- [ ]  `validate_file_path("repo", "src/main.py")` returns `repo/src/main.py`
- [ ]  `tools.py` contains `from app import server`
- [ ]  `pyproject.toml` exists and includes `gitpython` and `mcp`

## **5. Submit your task**

1. Commit your changes.
2. Push to GitHub.
3. Return to the lesson and click "Submit."
