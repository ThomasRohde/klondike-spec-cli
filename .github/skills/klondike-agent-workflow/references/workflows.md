# Klondike Session Workflows

Detailed patterns for managing agent sessions across context windows.

**Remember:** klondike does not use `--help` flags. Just run commands to see usage.

## Table of Contents

- [Complete Session Flow](#complete-session-flow)
- [First Session on a Project](#first-session-on-a-project)
- [Continuing Previous Work](#continuing-previous-work)
- [Feature Implementation Pattern](#feature-implementation-pattern)
- [Pre-Commit Workflow](#pre-commit-workflow)
- [Worktree Sessions](#worktree-sessions)
- [Multi-Agent Projects](#multi-agent-projects)

---

## Complete Session Flow

### Phase 1: Orientation (Always Do First)

```bash
# 1. Confirm location
pwd  # or Get-Location on Windows

# 2. Get project overview
klondike status

# 3. Check artifact health
klondike validate

# 4. Review recent git history
git log --oneline -10

# 5. Begin session
klondike session start --focus "F00X - description"
```

### Phase 2: Preparation

```bash
# 6. Run init script if present
./init.sh  # or .\init.ps1 on Windows

# 7. Verify dev server healthy
curl http://localhost:3000/health  # or appropriate health check

# 8. Mark feature in-progress
klondike feature start F00X
```

### Phase 3: Implementation

```bash
# Work in cycles:
# - Write code
# - Test incrementally
# - Commit atomically

git add -A
git commit -m "feat(scope): description"
```

### Phase 4: Verification

```bash
# 9. Run full test suite
uv run pytest  # or npm test

# 10. Capture evidence
# Save screenshots, logs, or test output to test-results/

# 11. Verify feature
klondike feature verify F00X --evidence "test-results/F00X-proof.png"
```

### Phase 5: Handoff

```bash
# 12. Ensure everything committed
git status  # Should be clean

# 13. End session
klondike session end \
  --summary "Implemented login form with validation" \
  --completed "Form UI,Validation logic,Error handling" \
  --next "Add password reset,Integrate with backend"
```

---

## First Session on a Project

When starting a brand new klondike project:

```bash
# 1. Initialize project
klondike init --name my-project --prd ./docs/prd.md

# 2. Add initial features
klondike feature add "Core functionality" -c core -p 1 \
  --criteria "Works end-to-end,Handles errors" \
  --notes "Start simple, iterate. Key files: src/main.py"

klondike feature add "User interface" -c ui -p 2 \
  --criteria "Responsive,Accessible" \
  --notes "Use React + Tailwind. Mobile-first."

# 3. View backlog
klondike feature list

# 4. Start session
klondike session start --focus "F001 - Core functionality"
```

---

## Continuing Previous Work

When returning to an existing project:

```bash
# 1. Get oriented (status shows last session and priority features)
klondike status

# Output shows:
# - Last session focus
# - In-progress features
# - Priority features
# - Git status

# 2. Check for any issues
klondike validate

# 3. Review what was in progress
klondike feature list --status in-progress

# 4. Start new session with same or new focus
klondike session start --focus "F001 - Continue login"
```

---

## Feature Implementation Pattern

### Small Feature (Single Session)

```bash
klondike feature start F001

# Implement...
# Test...

klondike feature verify F001 --evidence "test-output.log"
```

### Large Feature (Multi-Session)

**Session 1:**
```bash
klondike feature start F001
# Implement part 1...

klondike session end \
  --summary "Started F001, completed data layer" \
  --next "Implement UI layer,Add tests"
```

**Session 2:**
```bash
klondike status  # See where we left off
klondike session start --focus "F001 - Continue"
# F001 already in-progress, no need to start again

# Complete implementation...
# Full E2E test...

klondike feature verify F001 --evidence "e2e-test-results.png"
klondike session end --summary "Completed F001"
```

### Blocked Feature Recovery

```bash
# When blocked:
klondike feature block F001 --reason "Waiting for API endpoint"

# Start alternate feature
klondike feature start F002

# Later, when unblocked:
klondike feature start F001  # Resume
```

---

## Pre-Commit Workflow

### Step 1: Detect Stack

Check for project markers:

| File | Stack | Commands |
|------|-------|----------|
| `pyproject.toml` + `uv.lock` | Python (uv) | `uv run ...` |
| `pyproject.toml` only | Python (pip) | `python -m ...` |
| `package.json` | Node.js | `npm run ...` |
| `Cargo.toml` | Rust | `cargo ...` |
| `go.mod` | Go | `go ...` |

### Step 2: Run Checks

**Python (uv):**
```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest
```

**Node.js:**
```bash
npm run lint
npm run build
CI=true npm test  # PowerShell: $env:CI='true'; npm test
```

**Rust:**
```bash
cargo clippy
cargo fmt --check
cargo test
```

### Step 3: Record Results

Track what you ran before committing:

```markdown
| Command | Exit | Notes |
|---------|------|-------|
| `uv run ruff check` | 0 | ✅ |
| `uv run pytest` | 0 | 15 passed |
```

### Step 4: Commit or Fix

- All pass → `git commit -m "..."`
- Any fail → Fix issues, re-run, then commit

**Never leave the repository with failing tests.**

---

## Worktree Sessions

Isolated sessions using git worktrees for safe experimentation.

### Basic Worktree Session

```bash
# Start isolated session
klondike copilot start --worktree

# Work happens in ~/klondike-worktrees/project-name/session-id/
# Main project is untouched
```

### Feature-Focused Worktree

```bash
# Create worktree for specific feature
klondike copilot start -w --feature F001

# Creates branch: klondike/f001-<uuid>
# All work is isolated
```

### Apply Changes Back

```bash
# After completing work in worktree:
klondike copilot start -w --apply

# This:
# 1. Diffs worktree against original
# 2. Applies changes to main project
# 3. Cleans up worktree
```

### List and Cleanup

```bash
# See all active worktrees
klondike copilot list

# Clean up all worktrees
klondike copilot cleanup

# Force cleanup (uncommitted changes)
klondike copilot cleanup --force
```

### Worktree Directory Structure

```
~/klondike-worktrees/
└── my-project/
    ├── .klondike-project          # Links to original
    ├── f001-abc123/               # Feature worktree
    │   └── <full project copy>
    └── refactor-auth-def456/      # Named worktree
        └── <full project copy>
```

---

## Multi-Agent Projects

When project supports both Copilot and Claude:

### Initialize for Both

```bash
klondike init --agent all
```

Creates:
- `.github/` - Copilot templates
- `.claude/` + `CLAUDE.md` - Claude templates

### Add Agent Later

```bash
# Already have Copilot, add Claude
klondike upgrade --agent claude
```

### Agent-Specific Commands

**Claude Code:**
- Uses `/project:session-start` slash commands
- Reads `CLAUDE.md` at root
- Settings in `.claude/settings.json`

**GitHub Copilot:**
- Uses `klondike copilot start`
- Reads `.github/copilot-instructions.md`
- Templates in `.github/templates/`

### Both agents share:

- `.klondike/` directory
- Same features.json
- Same progress tracking
- Same verification requirements

---

## Session Checklist

Use before ending any session:

- [ ] All changes committed
- [ ] Tests passing
- [ ] No lint errors
- [ ] Features properly marked (started/verified/blocked)
- [ ] Evidence captured for verified features
- [ ] Session end command run with summary
- [ ] Next steps documented
