# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Inspired by [Anthropic's research on effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
>
> Managed by the `klondike` CLI tool - run `klondike` for available commands.

## Project Overview

Project: {{PROJECT_NAME}}
Created: {{DATE}}

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
- ❌ **Committing without running build checks first**
- ❌ **Committing without running tests first**
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

### Step 1: Detect Project Stack and Tools

Before running checks, detect available commands:

1. **Python with uv**: Check for `pyproject.toml` with `[tool.uv]` or `uv.lock`
   - Use `uv run` prefix for all commands
2. **Python with pip**: Check for `pyproject.toml`, `setup.py`, or `requirements.txt`
3. **Node.js**: Read `package.json` → look for `scripts.build`, `scripts.test`, `scripts.lint`
4. **Rust**: Check for `Cargo.toml`
5. **Go**: Check for `go.mod`

### Step 2: Run Detected Commands

| Check | Python (uv) | Python (pip) | Node.js | Rust | Go |
|-------|-------------|--------------|---------|------|----|
| Lint | `uv run ruff check src tests` | `ruff check` or `flake8` | `npm run lint` | `cargo clippy` | `golangci-lint` |
| Format | `uv run ruff format --check src tests` | `ruff format --check` | `npm run format` | `cargo fmt --check` | `gofmt -l` |
| Test | `uv run pytest` | `pytest` | `CI=true npm test` | `cargo test` | `go test` |
| Build | N/A (interpreted) | N/A | `npm run build` | `cargo build` | `go build` |

### Step 3: Record Results Before Commit

**You MUST record each command's result:**

```markdown
#### Pre-Commit Verification
| Command | Exit Code | Notes |
|---------|-----------|-------|
| <lint command> | 0 | ✅ |
| <format command> | 0 | ✅ |
| <test command> | 0 | ✅ N tests passed |
```

### Step 4: Commit Only If All Pass

If you skip verification and a build/test fails after commit:
1. Immediately fix the issue
2. Amend the commit or create a fix commit
3. Never leave the repository in a broken state

## Custom Slash Commands

This project includes custom slash commands in `.claude/commands/`:

- `/session-start` - Start a new coding session with proper context gathering
- `/session-end` - End session with documentation and clean state
- `/verify-feature` - Verify a feature is complete with evidence
- `/progress-report` - Generate a comprehensive progress report
- `/add-features` - Add new features to the registry
- `/init-project` - Initialize project infrastructure
- `/recover-from-failure` - Diagnose and recover from broken state

Run a command by typing `/project:command-name` in Claude Code.

## Klondike CLI Quick Reference

```bash
# Project status
klondike status              # Project overview
klondike validate            # Check artifact integrity

# Feature management
klondike feature list        # List all features
klondike feature add "..."   # Add new feature
klondike feature start F00X  # Mark in-progress
klondike feature verify F00X # Mark verified
klondike feature block F00X  # Mark blocked

# Session management
klondike session start       # Start new session
klondike session end         # End with summary
klondike progress            # Show/regenerate progress
```

## Artifact Rules

### .klondike/features.json - MANAGED BY CLI

**Use these commands:**
- `klondike feature add "description" --category X --priority N --criteria "..." --notes "..."` - Add feature
- `klondike feature start F00X` - Mark in-progress
- `klondike feature verify F00X --evidence "..."` - Mark verified
- `klondike feature block F00X --reason "..."` - Mark blocked
- `klondike feature list` - List all features
- `klondike feature show F00X` - Show feature details

> **⚠️ Always use `--notes`** when adding features. Include: implementation approach,
> edge cases, dependencies, and gotchas. A weaker agent will implement—give them context.

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
