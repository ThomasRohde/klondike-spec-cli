# GitHub Copilot CLI: Running, Customizing, and Orchestrating from Python

> Opinionated, developer‑ready guide for using GitHub Copilot CLI as a controllable coding agent from scripts and agent frameworks (e.g. Klondike Spec).

Status: **Dec 2025**, Copilot CLI public preview. Details may change — always double‑check with `copilot help` and the official docs when upgrading.

---

## 1. Mental model of Copilot CLI

GitHub Copilot CLI is essentially the **Copilot coding agent in your terminal**:

- It runs as a Node‑based CLI: `npm install -g @github/copilot`.
- It uses the same agent harness as Copilot coding agent on GitHub.
- It reads **repository custom instructions** and **custom agents** from your repo.
- It stores global config in `~/.copilot` (or in `$XDG_CONFIG_HOME` if set). citeturn5view0turn2view1

For Klondike, you should think of Copilot CLI as a **remote-controlled coding worker** that you launch in a prepared Git worktree, with:

- Known **context**: repo, branch, instructions, agents.
- Known **guardrails**: permissions, allow/deny tools, trusted folders.
- A **single prompt** (`-p/--prompt`) or an interactive chat session.

---

## 2. Installation, versioning, and basic check

### 2.1 Install / upgrade

```bash
npm install -g @github/copilot
```

Check version:

```bash
copilot --version
```

If you see very old version output or the command is missing, reinstall or ensure the correct `npm` global bin directory is on your `PATH`. citeturn5view0

### 2.2 Sanity test

In a small scratch repo:

```bash
mkdir copilot-test && cd copilot-test
git init
echo 'console.log("hello");' > index.js
copilot
```

- Approve the folder.
- Run a simple prompt like “Add a function that returns the sum of two numbers.”

If this doesn’t work reliably, **stop here and fix the environment** before wiring it into Python.

---

## 3. How Copilot CLI picks up repository context

Copilot CLI automatically pulls in *three* main sources of repository context when you start it in a folder that’s inside a Git repo: citeturn2view1turn7view0

1. **Repository custom instructions**  
   - Global project instructions:  
     - `.github/copilot-instructions.md`
   - Path‑specific instructions (for large repos):  
     - `.github/copilot-instructions/**/*.instructions.md`  
       – e.g. `.github/copilot-instructions/backend.instructions.md`  
       – e.g. `.github/copilot-instructions/frontend.instructions.md`
   - These are *always* included in prompts for that repo and path.

2. **Agent configuration**  
   - Repository‑level custom agents in:  
     - `.github/agents/*.agent.md`  
   - Global/user agents in:  
     - `~/.copilot/agents/*.agent.md`  
   - Extra instructions via `AGENTS.md` at repo root (for standard agent set‑up).

3. **GitHub repository context**  
   - Issues, PRs, branches, etc. when authenticated.

This is explicitly documented for Copilot CLI: citeturn2view1turn7view0

> Copilot CLI supports:
> - `.github/copilot-instructions.md`
> - `.github/copilot-instructions/**/*.instructions.md`
> - `AGENTS.md`
> - `.github/agents` for custom agents

### 3.1 Why your instructions may *seem* ignored

Common failure modes:

1. **Wrong working directory from Python**  
   - CLI only sees repo instructions if the current working directory (`cwd`) is *inside* the Git repo.
   - If your Python code runs `copilot` from a parent folder (or a tmp dir), the repo is invisible.

2. **Wrong paths / filenames**  
   - Must be exactly:
     - `.github/copilot-instructions.md` **(hyphen, not underscore)**  
     - `.github/copilot-instructions/<anything>.instructions.md`
   - Case‑sensitive on Linux/macOS.

3. **Old CLI version**  
   - Early builds did not fully support all instruction locations.
   - Upgrade with `npm install -g @github/copilot@latest` and re‑test.

4. **Multiple repos / worktrees**  
   - If you spawn Copilot from a worktree, make sure `.git` correctly points to the original repo and the `.github` folder is reachable from that worktree.

5. **Org / policy restrictions**  
   - If your Copilot org admin has restricted features, some behaviour may differ. Check `copilot help environment` and org policies.

**Quick test inside the repo** (manually in terminal):

```bash
cd /path/to/repo
copilot
```

Ask:

> “Summarize our project’s coding guidelines from the repository instructions.”

If it gives a reasonable summary of `.github/copilot-instructions.md`, your instructions are being read correctly. If not, fix this *before* involving Python or agents.

---

## 4. Custom agents: `.github/agents` and `AGENTS.md`

Custom agents are specialized versions of the Copilot coding agent with their own role, tools, and prompts, defined as Markdown “agent profiles” in your repo: citeturn2view1turn0search6

- Repository‑level agent profiles live in:  
  `.github/agents/<agent-name>.agent.md`

Each file describes:

- Agent name and description.
- Default prompts / behaviour.
- Tools / MCP servers it can use.

You can use these agents from Copilot CLI in **three ways**: citeturn2view1

1. **Interactive, via `/agent`**  
   - Start `copilot` and run `/agent`, then select your custom agent.

2. **Implicitly, by name in the prompt**  
   - “Use the *refactoring agent* to refactor this module…”.  
   - It will try to infer which agent you mean.

3. **Non‑interactive, via CLI flag**  
   - `copilot --agent=klondike-feature-dev --prompt "Implement feature XYZ"`

For Klondike:

- Put **general Klondike guidance** in `.github/copilot-instructions.md`.
- Put **behavioural agent profiles** in `.github/agents/klondike-*.agent.md`.
- Optionally add an `AGENTS.md` at repo root that documents your agents for humans.

---

## 5. Configuration files and environment variables

Copilot CLI stores persistent config under `~/.copilot` (or `$XDG_CONFIG_HOME`): citeturn2view1turn6search5

- `~/.copilot/config.json` – global CLI configuration.
- `~/.copilot/mcp-config.json` – MCP server definitions.
- `~/.copilot/agents` – user‑level custom agents.

Useful commands (check them once and read the output):

```bash
copilot help config
copilot help environment
copilot help logging
copilot help permissions
```

Community docs and guides confirm additional behaviour: citeturn6search14turn6search19

- **Model selection** via environment, e.g.:

  ```bash
  export COPILOT_MODEL=gpt-5
  copilot
  ```

- **Programmatic prompts** via `-p` / `--prompt`:

  ```bash
  copilot -p "run tests and fix any failures"
  ```

- **Tool permissions** via CLI flags (subject to change):

  ```bash
  copilot -p "run tests and fix failures"     --allow-tool=git --allow-tool=npm     --deny-tool=rm --deny-tool=sudo
  ```

For any of these, the **source of truth** is `copilot help` in your installed version.

---

## 6. Programmatic / non‑interactive mode

Although Copilot CLI is designed primarily for interactive use, it supports a **single‑prompt “programmatic mode”** where you pass a prompt as an argument and let it run to completion. Community guides and GitHub’s own blogs show patterns like: citeturn7view0turn4search17

```bash
# One‑shot programmatic prompt
copilot -p "run the test suite and fix any failing tests"

# With a specific agent
copilot --agent=klondike-feature-dev   --prompt "Implement the login feature according to our instructions"

# With pre‑approved tools for automation
copilot -p "update dependencies and test compatibility"   --allow-tool=git --allow-tool=npm
```

**Characteristics of programmatic mode**:

- No interactive TUI; it runs until completion and exits.
- Exit code is non‑zero on failures (e.g., fatal errors, permissions problems).
- Output is printed to stdout/stderr (you can capture it in Python).

This is the mode you want for **Klondike‑driven automation**.

---

## 7. Running Copilot CLI from Python

Below are patterns that work well for an agent framework.

### 7.1 Minimal helper: `run_copilot_once`

```python
import os
import subprocess
from pathlib import Path
from typing import Iterable, Optional

def run_copilot_once(
    prompt: str,
    *,
    repo_path: str | Path,
    agent: Optional[str] = None,
    allow_tools: Iterable[str] = (),
    deny_tools: Iterable[str] = (),
    extra_env: Optional[dict] = None,
    model: Optional[str] = None,
    timeout: Optional[int] = 60 * 30,  # 30 min
) -> subprocess.CompletedProcess[str]:
    """Run a single Copilot CLI prompt non-interactively and return the CompletedProcess."""
    repo_path = Path(repo_path).resolve()

    cmd: list[str] = ["copilot"]

    # Programmatic prompt
    cmd += ["-p", prompt]

    # Optional agent
    if agent:
        cmd += [f"--agent={agent}"]

    # Permissions
    for tool in allow_tools:
        cmd += [f"--allow-tool={tool}"]
    for tool in deny_tools:
        cmd += [f"--deny-tool={tool}"]

    # Environment
    env = os.environ.copy()
    if model:
        env["COPILOT_MODEL"] = model
    if extra_env:
        env.update(extra_env)

    result = subprocess.run(
        cmd,
        cwd=str(repo_path),
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
    )

    return result
```

**Key points**:

- `cwd` is set to `repo_path` so Copilot CLI sees the `.git` repo and `.github` instructions.
- You can choose a custom `agent`, `allow_tools`, `deny_tools`, and `model` per call.
- The calling code can inspect `result.returncode`, `result.stdout`, and `result.stderr`.

Typical usage:

```python
from textwrap import dedent

prompt = dedent("""
    You are the Klondike feature implementation agent.
    - Read the feature description in AGENTS.md or the feature spec files.
    - Implement the feature end-to-end.
    - Run tests and fix any failures.
    - Leave clear TODOs for anything you can't complete.
""")

result = run_copilot_once(
    prompt,
    repo_path="/path/to/klondike-worktree",
    agent="klondike-feature-dev",
    allow_tools=["git", "npm", "pnpm", "node"],
    deny_tools=["rm", "sudo"],
    model="gpt-5",
)

if result.returncode != 0:
    raise RuntimeError(
        f"Copilot CLI failed ({result.returncode}):\n{result.stderr}"
    )

print(result.stdout)
```

### 7.2 Handling TUI / ANSI output

Even in programmatic mode, Copilot CLI may emit **ANSI control sequences** and status lines.

If you want to **post‑process** the output (for logs or other agents), you can strip ANSI codes with a small helper:

```python
import re

ANSI_RE = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")

def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)
```

Then:

```python
clean_stdout = strip_ansi(result.stdout)
clean_stderr = strip_ansi(result.stderr)
```

### 7.3 Timeouts and failure handling

- Set a **reasonable timeout** per task (e.g. 10–30 minutes for heavy work).
- Treat non‑zero exit codes as **agent failure** and capture logs for debugging.
- Consider including the **raw prompt and sanitized output** in your Klondike artifacts.

---

## 8. Recommended repo layout for Copilot + Klondike

For a Copilot‑friendly Klondike test repo, something like:

```text
.
├─ .git/
├─ .github/
│  ├─ copilot-instructions.md
│  ├─ copilot-instructions/
│  │  ├─ backend.instructions.md
│  │  └─ frontend.instructions.md
│  └─ agents/
│     ├─ klondike-feature-dev.agent.md
│     └─ klondike-refactorer.agent.md
├─ AGENTS.md
├─ klondike/
│  ├─ features/          # Klondike feature specs
│  └─ prompts/           # Prompt templates
└─ src/
   └─ ...
```

Suggested content:

- **`.github/copilot-instructions.md`**  
  - Overall domain language, conventions, testing rules, branch naming, etc.

- **Path‑specific instructions**  
  - `backend.instructions.md`, `frontend.instructions.md`, `docs.instructions.md` for large repos.

- **`.github/agents/*.agent.md`**  
  - One agent per role (feature implementation, refactoring, test creation, etc.).

- **`AGENTS.md`**  
  - Human‑readable description of agents and how they are intended to be used.

This repository shape matches how GitHub’s own docs and community guides describe Copilot CLI’s repository integration. citeturn2view1turn7view0

---

## 9. Permissions, trust and safety when scripted

When you run Copilot CLI non‑interactively from Python, you must be **explicit about what it’s allowed to do**.

Key levers: citeturn2view1turn7view0turn6search0turn6search19

1. **Trusted directories**  
   - Defined in `~/.copilot/config.json` under `trusted_folders`.
   - You can pre‑trust your **worktree root** to avoid interactive prompts.

2. **Tool permissions**  
   - `copilot help permissions` explains your version’s model.
   - Community guides show flags like:
     - `--allow-tool=<name>`
     - `--deny-tool=<name>`
     - `--allow-all-tools`
   - For fully automated flows, **never** blanket‑allow destructive tools (e.g. `rm`, `sudo`).

3. **Custom instructions**  
   - Use `.github/copilot-instructions.md` to declare allowed operations, e.g.:
     - “Do not touch files under `infra/`”
     - “Never modify GitHub Actions workflows automatically”

4. **MCP servers**  
   - Extra external capabilities are configured via `~/.copilot/mcp-config.json` or `/mcp add`.  
   - Treat them as additional “tools” from a security perspective.

5. **Environment scoping**  
   - Use dedicated GitHub tokens or limited‑scope PATs via `GITHUB_TOKEN` / `GH_TOKEN` for automated runs.

---

## 10. Worktree pattern for Klondike (high level)

A pattern that works well for autonomous feature work (you’ve already started down this road):

1. **Create a temporary worktree and branch** per feature.

   ```bash
   git worktree add ../repo-klondike-feature-123 -b feature/klondike-123
   ```

2. **Run Copilot CLI from Python inside that worktree** using `run_copilot_once()`.

3. When Copilot is done:
   - Run tests / linters from Python.
   - If acceptable, commit and optionally squash.
   - Merge the feature branch back to main.

This keeps Copilot’s edits **isolated** while still fully leveraging repo instructions and agents.

---

## 11. Debugging when Copilot CLI doesn’t behave as expected

Checklist when something feels off:

1. **Confirm instructions are seen**  
   - Start an interactive `copilot` in the repo and ask it to summarize your instructions.

2. **Dump environment**  
   - Run `copilot help environment` and check for any env vars that might disable features or change behaviour.

3. **Inspect config**  
   - Open `~/.copilot/config.json` and verify `trusted_folders`, model, logging level, etc.

4. **Increase logging**  
   - Use `copilot help logging` to see available levels and bump to a verbose level for debugging.

5. **Reproduce manually**  
   - If a Python‑spawned run misbehaves, try the *same prompt and flags* manually in the shell from the same `cwd`.

6. **Keep CLI current**  
   - Reinstall regularly while it’s in preview: `npm install -g @github/copilot`.

---

## 12. How to use this document in Klondike

A practical approach:

- Check this into a repo as `COPILOT-CLI-RUNBOOK.md`.
- Add a short prompt template in your Klondike spec that tells Copilot:

  > “When you are invoked from Klondike, assume the setup described in `COPILOT-CLI-RUNBOOK.md` and follow its conventions.”

- Use the `run_copilot_once()` helper as the **single abstraction layer** to spawn Copilot CLI instances from Python.

If you want, we can follow up by:

- Designing a **Klondike‑specific agent profile** (`klondike-feature-dev.agent.md`).
- Defining a **small JSON/YAML spec** for “Copilot task” that your Python code turns into CLI flags + prompts.
