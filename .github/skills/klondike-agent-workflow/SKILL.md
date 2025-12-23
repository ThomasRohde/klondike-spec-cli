---
name: klondike-agent-workflow
description: Manage multi-session AI agent workflows using klondike CLI. Use when working on klondike-managed projects (those with .klondike/ directory), when starting/ending coding sessions, tracking features through lifecycle, or maintaining coherence across context window resets. Triggers on session management, feature tracking, progress handoffs, and verification workflows.
---

# Klondike Agent Workflow

Klondike bridges context windows for long-running agent sessions. **Always use CLI commands—never read .klondike/*.json files directly.**

## Quick Decision Tree

```
Starting work?     → klondike status → klondike session start --focus "F00X"
Working on feature → klondike feature start F00X
Feature complete?  → Test E2E → klondike feature verify F00X --evidence "..."
Blocked?           → klondike feature block F00X --reason "..."
Ending session?    → klondike session end --summary "..." --next "..."
```

## Session Lifecycle

### 1. Session Start (Do First!)

```bash
klondike status                                    # See project state
klondike validate                                  # Check artifact integrity
klondike session start --focus "F001 - Login UI"  # Begin session
klondike feature start F001                        # Mark feature in-progress
```

### 2. During Work

- **One feature at a time** (tracked by `feature start`)
- Commit after each meaningful change
- Test incrementally, not at end
- If blocked: `klondike feature block F00X --reason "..."`

### 3. Session End (Before Leaving!)

```bash
klondike feature verify F00X --evidence "test-results/F00X.png"
klondike session end --summary "Done" --next "Implement logout"
```

## Feature Workflow

| Action | Command |
|--------|---------|
| Add | `klondike feature add "desc" -c core -p 1 --criteria "..." --notes "..."` |
| Start | `klondike feature start F001` |
| Block | `klondike feature block F001 --reason "Needs API"` |
| Verify | `klondike feature verify F001 --evidence "path/to/proof"` |
| Show | `klondike feature show F001` |
| List | `klondike feature list --status in-progress` |

## Critical Rules

**DO:**
- Use `klondike status` before any work
- Use `klondike feature list` to see features (not file reads)
- Include `--notes` when adding features (helps future agents)
- Capture evidence before verifying
- Run pre-commit checks before committing

**DON'T:**
- Read `.klondike/*.json` files directly
- Edit `agent-progress.md` manually
- Mark features verified without E2E testing
- Leave session without `session end`
- Work on multiple features simultaneously

## Pre-Commit Verification

Before every commit:

```bash
# Python (uv)
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest

# Node.js
npm run lint && npm run build && CI=true npm test
```

Only commit if all pass. Never leave repo broken.

## Reference Files

- **[commands.md](references/commands.md)**: Complete CLI reference with all options
- **[workflows.md](references/workflows.md)**: Detailed session patterns and examples
- **[troubleshooting.md](references/troubleshooting.md)**: Common issues and recovery
