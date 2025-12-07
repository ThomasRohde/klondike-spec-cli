# Long-Running Agent Harness Instructions

> Inspired by [Anthropic's research on effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

## Core Philosophy

This repository uses a **multi-context-window agent workflow** designed to maintain coherence across long-running coding sessions. The key insight: each agent session starts fresh, so we create structured artifacts that bridge context windows.

## Required Artifacts

### 1. Progress File (`agent-progress.md`)
- **Purpose**: Handoff document between agent sessions
- **Location**: Project root
- **Update frequency**: End of every meaningful work session
- **Content**: What was done, what's next, any blockers

### 2. Feature Registry (`features.json`)
- **Purpose**: Prevent premature "victory declaration" and track completion
- **Location**: Project root
- **Rules**: 
  - Only change `passes` field (never delete or edit test descriptions)
  - Must be verified end-to-end before marking `passes: true`

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
2. Read `agent-progress.md` to understand recent work
3. Check `git log --oneline -10` for recent commits
4. Read `features.json` to identify next priority
5. Run `init.sh`/`init.ps1` to start dev environment
6. Run basic smoke test before new work

### During a Session
- Work on **ONE feature at a time**
- Make atomic, reviewable commits with descriptive messages
- Test incrementally - don't batch testing to the end
- If you hit a blocker, document it and move to next task

### Ending a Session
1. Ensure code compiles/passes linting
2. Commit all changes with clear messages
3. Update `agent-progress.md` with:
   - What was accomplished
   - What was attempted but didn't work
   - Recommended next steps
4. Update `features.json` only for verified features
5. Leave the environment in a **clean, mergeable state**

## Prohibited Behaviors

- ❌ One-shotting complex features
- ❌ Declaring project complete without checking `features.json`
- ❌ Removing or editing feature descriptions in `features.json`
- ❌ Leaving code in broken/half-implemented state
- ❌ Making changes without committing and documenting
- ❌ Marking features as passing without end-to-end verification
- ❌ **Committing without running `npm run build` first**
- ❌ **Committing without running `npm run test` first**
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
1. Check if `agent-progress.md` exists - read it for context
2. Check if `features.json` exists - identify current priorities
3. **Run Artifact Integrity Checks** (see below)
4. Review `git log --oneline -10` for recent changes
5. If init script exists, run it and verify health checks pass
6. Create a **Session Plan** (3-6 steps with status tracking)
7. Announce which feature you'll work on

### Artifact Integrity Checks (MANDATORY)

Before coding, validate artifacts are consistent:

**features.json checks:**
- File exists and is valid JSON
- `metadata.totalFeatures` matches actual feature count
- `metadata.passingFeatures` matches count where `passes: true`
- No features have been deleted (compare IDs to previous session if noted)
- All required fields present: `id`, `description`, `acceptanceCriteria`, `passes`

**agent-progress.md checks:**
- File exists
- Session numbers are monotonically increasing
- No previous session entries have been deleted or modified

**If inconsistencies found:**
1. **STOP** - do not proceed with coding
2. Document the inconsistency
3. Fix the artifact or invoke `/recover-from-failure`
4. Only continue after integrity is restored

### While Working

1. Focus on ONE feature from `features.json` at a time
2. Commit after each meaningful change
3. Test as you go, not at the end
4. If something breaks, fix it before continuing

### Before Ending Work

When the user indicates they're done or switching tasks:
1. Ensure all changes are committed
2. Update `agent-progress.md` with session summary
3. Update `features.json` only for verified-complete features
4. Summarize the handoff for the next session

---

## Quick Reference: Artifact Rules

### features.json - STRICT RULES

**Allowed:**
- Change `status` field (`not-started` → `in-progress` → `blocked` | `verified`)
- Change `passes` from `false` to `true` (after verification)
- Set `verifiedAt` timestamp
- Set `verifiedBy` identifier
- Set `evidenceLinks` array with paths to verification evidence
- Set `blockedBy` (feature IDs or reason string)
- Set `lastWorkedOn` timestamp
- Add `notes` for context

**Forbidden:**
- Delete features
- Edit `description` or `acceptanceCriteria`
- Mark as passing without end-to-end testing
- Change `status` to `verified` without evidence

### agent-progress.md - APPEND ONLY

**Allowed:**
- Append new session entries
- Update "Quick Reference" section

**Forbidden:**
- Delete previous session entries
- Modify historical records

---

## Initialization Checklist

For new projects using this workflow, ensure these exist:
- [ ] `features.json` with comprehensive feature list (20+ features)
- [ ] `agent-progress.md` with initial session entry
- [ ] `init.sh` and/or `init.ps1` for environment setup
- [ ] Initial git commit with clean state
- [ ] `.vscode/settings.json` with Copilot configuration
