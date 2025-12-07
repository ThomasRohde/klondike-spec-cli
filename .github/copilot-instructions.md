# Klondike Spec Agent Instructions

> Inspired by [Anthropic's research on effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
> 
> Managed by the `klondike` CLI tool - run `klondike` for available commands.

## Core Philosophy

This repository uses a **multi-context-window agent workflow** designed to maintain coherence across long-running coding sessions. The key insight: each agent session starts fresh, so we create structured artifacts that bridge context windows.

## Required Artifacts

### 1. Progress File (`agent-progress.md`)
- **Purpose**: Handoff document between agent sessions
- **Location**: Project root (auto-generated from `.klondike/agent-progress.json`)
- **Update frequency**: Automatically updated by `klondike session end`
- **Content**: What was done, what's next, any blockers

### 2. Feature Registry (`.klondike/features.json`)
- **Purpose**: Prevent premature "victory declaration" and track completion
- **Location**: `.klondike/` directory
- **Managed by**: `klondike feature` commands
- **Rules**: 
  - Use `klondike feature verify F00X` to mark as passing
  - Use `klondike feature start F00X` to begin work
  - Never manually edit - use CLI commands

### 3. Init Script (`init.sh` / `init.ps1`)
- **Purpose**: Reproducible environment startup
- **Location**: Project root
- **Must include**: 
  - Dev server startup **in background** (using `&` in bash, `Start-Job` in PowerShell)
  - Health checks with timeout
  - Clean exit after server is ready (script should NOT block waiting for server)

## Agent Behavior Rules

### Starting a Session
1. Run `pwd` / `Get-Location` to confirm working directory
2. Run `klondike status` to see project overview and recent work
3. Run `klondike validate` to check artifact integrity
4. Check `git log --oneline -10` for recent commits
5. Run `klondike session start --focus "F00X - description"` to begin
6. Run `init.sh`/`init.ps1` if project has dev server
7. Run basic smoke test before new work

### During a Session
- Work on **ONE feature at a time** - use `klondike feature start F00X` to track
- Make atomic, reviewable commits with descriptive messages
- Test incrementally - don't batch testing to the end
- If you hit a blocker, use `klondike feature block F00X --reason "..."` and move to next task

### Ending a Session
1. Ensure code compiles/passes linting
2. Commit all changes with clear messages
3. For verified features, run `klondike feature verify F00X --evidence "..."`
4. Run `klondike session end --summary "What was accomplished" --next "Recommended next steps"`
5. Leave the environment in a **clean, mergeable state**

## Prohibited Behaviors

- ❌ One-shotting complex features
- ❌ Declaring project complete without running `klondike status`
- ❌ Manually editing `.klondike/features.json` (use CLI commands)
- ❌ **Reading `.klondike/*.json` or `agent-progress.md` directly** (use CLI commands)
- ❌ Leaving code in broken/half-implemented state
- ❌ Making changes without committing and documenting
- ❌ Using `klondike feature verify` without end-to-end verification
- ❌ **Committing without running `npm run build` first** (or equivalent)
- ❌ **Committing without running `npm run test` first** (or equivalent)
- ❌ **Leaving the repository with failing builds or tests**

## Testing Standards

- Always verify features as a user would (end-to-end)
- For web apps: use browser automation / screenshots
- For APIs: test actual endpoints, not just unit tests
- For CLI tools: run actual commands, check output
- Document any testing limitations in progress file

## Git Hygiene

- Commit early, commit often
- Use conventional commit messages
- Tag stable checkpoints
- Use `git revert` to recover from bad changes
- Never force push without documenting why

## Pre-Commit Verification (MANDATORY)

### Step 1: Detect Project Stack

Before running checks, detect available commands:

1. Read `package.json` → look for `scripts.build`, `scripts.test`, `scripts.lint`
2. If Python: check for `pyproject.toml`, `setup.py`, or `requirements.txt`
3. If Rust: check for `Cargo.toml`
4. If Go: check for `go.mod`

### Step 2: Run Detected Commands

| Check | Node.js | Python | Rust | Go |
|-------|---------|--------|------|----|
| Build | `npm run build` | `python -m py_compile` | `cargo build` | `go build` |
| Test | `npm test` | `pytest` | `cargo test` | `go test` |
| Lint | `npm run lint` | `ruff check` or `flake8` | `cargo clippy` | `golangci-lint` |

### Step 3: Record Results Before Commit

**You MUST record each command's result:**

```markdown
#### Pre-Commit Verification
| Command | Exit Code | Notes |
|---------|-----------|-------|
| npm run build | 0 | ✅ |
| npm test | 0 | ✅ 42 tests passed |
| npm run lint | 0 | ✅ |
```

**If a command is missing from the project:**
- Note its absence in `agent-progress.md` Technical Notes
- Example: "No lint script configured - recommend adding eslint"
- Do NOT silently skip

### Step 4: Commit Only If All Pass

```
Detect stack → Run build → Run tests → Run lint → Record results → All pass? → Commit
                  ↓           ↓           ↓
              Fix errors  Fix tests  Fix lint
                  ↓           ↓           ↓
              Re-run    → Re-run   → Re-run  → Record → All pass? → Commit
```

**If you skip verification and a build/test fails after commit:**
1. Immediately fix the issue
2. Amend the commit or create a fix commit
3. Never leave the repository in a broken state

---

## Session Lifecycle (Embedded Behavior)

When working on this project, automatically follow these patterns:

### On First Interaction of a Session

Before doing any coding work:
1. Run `klondike status` to see project overview
2. Run `klondike validate` to check artifact integrity
3. Review `git log --oneline -10` for recent changes
4. Run `klondike session start --focus "F00X - description"` to begin session
5. If init script exists, run it and verify health checks pass
6. Create a **Session Plan** (3-6 steps with status tracking)
7. Use `klondike feature start F00X` to mark which feature you'll work on

### Artifact Integrity Checks (MANDATORY)

Run `klondike validate` which automatically checks:

**features.json checks:**
- File exists and is valid JSON in `.klondike/` directory
- `metadata.totalFeatures` matches actual feature count
- `metadata.passingFeatures` matches count where `passes: true`
- All required fields present: `id`, `description`, `acceptanceCriteria`, `passes`

**agent-progress.json checks:**
- File exists in `.klondike/` directory
- Valid JSON structure

**If inconsistencies found:**
1. **STOP** - do not proceed with coding
2. Document the inconsistency
3. Fix the artifact or investigate the issue
4. Only continue after `klondike validate` passes

### While Working

1. Focus on ONE feature at a time (tracked via `klondike feature start F00X`)
2. Commit after each meaningful change
3. Test as you go, not at the end
4. If something breaks, fix it before continuing

### Before Ending Work

When the user indicates they're done or switching tasks:
1. Ensure all changes are committed
2. Use `klondike feature verify F00X --evidence "..."` for verified features
3. Run `klondike session end --summary "..." --next "..."`
4. Summarize the handoff for the next session

---

## Quick Reference: Artifact Rules

### .klondike/features.json - MANAGED BY CLI

**Use these commands:**
- `klondike feature add "description" --category X --priority N --criteria "..."` - Add feature
- `klondike feature start F00X` - Mark in-progress
- `klondike feature verify F00X --evidence "..."` - Mark verified
- `klondike feature block F00X --reason "..."` - Mark blocked
- `klondike feature list` - List all features
- `klondike feature show F00X` - Show feature details

**Forbidden:**
- Manually editing `.klondike/features.json`
- **Reading `.klondike/features.json` directly** (use `klondike feature list` or `klondike feature show`)
- Deleting features
- Marking as passing without end-to-end testing

### agent-progress.md - AUTO-GENERATED

This file is automatically generated by the klondike CLI from `.klondike/agent-progress.json`.

**Use these commands:**
- `klondike session start --focus "..."` - Start new session
- `klondike session end --summary "..." --next "..."` - End session with summary
- `klondike progress` - Regenerate and display progress file

**Do not manually edit** - changes will be overwritten.

---

## Initialization Checklist

For new projects using this workflow:

```bash
# Install klondike CLI
pip install klondike-spec-cli

# Initialize project
klondike init <project-name>

# Add features (20+ recommended)
klondike feature add "Feature description" --category core --priority 1 --criteria "..."

# Verify setup
klondike status
klondike validate
```

Ensures:
- [ ] `.klondike/features.json` with comprehensive feature list (20+ features)
- [ ] `.klondike/agent-progress.json` for session tracking
- [ ] `agent-progress.md` auto-generated at project root
- [ ] `init.sh` and/or `init.ps1` for environment setup (if dev server)
- [ ] Initial git commit with clean state
- [ ] `.vscode/settings.json` with Copilot configuration
