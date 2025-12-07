---
name: session-start
description: "Start a new coding session with proper context gathering"
---

# Goal

Execute the **standardized startup routine** for a long-running agent session, ensuring you have full context before making any changes.

## Context

This prompt implements the "Getting up to speed" phase from Anthropic's long-running agent research. Every coding session should start with this routine to:
- Understand current project state
- Identify what was done recently
- Verify the environment works
- Choose the right next task

## Instructions

### 1. Orient Yourself

```bash
# Confirm working directory
pwd  # or Get-Location on Windows

# Check project structure
ls -la  # or Get-ChildItem
```

### 2. Read Progress Artifacts

Read these files in order:

1. **`agent-progress.md`** - Recent session summaries
   - What was the last session working on?
   - Are there any documented blockers?
   - What were the recommended next steps?

2. **`features.json`** - Feature completion status
   - How many features are passing vs pending?
   - What's the highest priority incomplete feature?
   - Are there any features marked as `in-progress` or `blocked`?

3. **Git history** - Recent changes
   ```bash
   git log --oneline -15
   git status
   git diff --stat HEAD~3  # What changed recently
   ```

### 3. Artifact Integrity Checks (MANDATORY)

Before proceeding, validate:

**features.json:**
- [ ] File is valid JSON
- [ ] `metadata.totalFeatures` == actual feature count
- [ ] `metadata.passingFeatures` == count where `passes: true`
- [ ] All features have required fields: `id`, `description`, `acceptanceCriteria`, `passes`
- [ ] No features from previous session are missing (compare with `agent-progress.md` if noted)

**agent-progress.md:**
- [ ] Session numbers are sequential (no gaps or duplicates)
- [ ] Previous session entries are intact (not deleted/modified)

**If any check fails:**
1. Document the inconsistency in output
2. Fix immediately before any coding work
3. If unfixable, invoke `/recover-from-failure`

### 4. Start the Environment

**IMPORTANT**: The init script starts the dev server **in the background** and performs health checks. If the health checks fail, do NOT proceed.

```bash
# Run the init script (it handles server startup and health checks)
./init.sh  # or .\init.ps1 on Windows
```

The init script will:
1. Kill any stale dev servers on the target port
2. Install dependencies if missing
3. Run type check, lint, and tests
4. **Start dev server in background** (won't block the agent)
5. Wait for port to be ready (health check with timeout)
6. Run a minimal smoke test
7. Exit cleanly after health check passes

**Note**: The dev server continues running in the background after the script exits. This is intentional—it allows the agent to proceed with coding work without being blocked by the server process.

**If init script fails:**
- **STOP** - Do not start new features
- Document the failure
- Invoke `/recover-from-failure` to diagnose and fix
- Only continue after init passes completely

### 5. Smoke Test

Before implementing new features, verify basic functionality:

- **For web apps**: Navigate to main page, perform core action
- **For APIs**: Hit health endpoint, test one main endpoint
- **For CLI tools**: Run help command, execute basic operation
- **For libraries**: Run test suite, import main module

If smoke test fails:
- **STOP** - Do not start new features
- Investigate and fix the existing issue first
- Document what was broken in progress file

### 6. Create Session Plan

Before starting work, create a plan with 3-6 concrete steps:

```markdown
#### Session Plan
| # | Task | Status |
|---|------|--------|
| 1 | <specific task> | in-progress |
| 2 | <specific task> | not-started |
| 3 | <specific task> | not-started |
```

**Status values:** `not-started`, `in-progress`, `blocked`, `done`

**Rules:**
- Only ONE task `in-progress` at a time
- Update status as you complete each task
- If blocked, note the reason and move to next task
- At session end, all tasks must be `done` or explicitly `blocked` with owner/next-step

### 7. Select Next Task

Based on your review:

1. If environment is broken → Fix it first
2. If there are incomplete in-progress features → Complete them
3. Otherwise → Pick highest priority feature from `features.json`

### 8. Announce Your Plan and Begin

Before making changes, state:
- Which feature you'll work on (by ID and description)
- Your approach in 2-3 sentences
- Any risks or dependencies you've identified

**Then immediately begin implementation.** Do not wait for user confirmation—the purpose of this prompt is to get up to speed AND start working.

## Output Format

After completing the startup routine, provide a brief status report and **begin coding immediately**:

```markdown
## Session Start Report

**Timestamp**: <current time>
**Working Directory**: <path>

### Artifact Integrity
- [x] features.json valid (X features, Y passing)
- [x] Metadata counts match actual
- [x] agent-progress.md sessions sequential
- [x] No missing features detected

### Environment Status
- [x] Init script executed
- [x] Health checks passed
- [x] Smoke test passed

### Project Status
- **Total Features**: X
- **Passing**: Y (Z%)
- **In-Progress**: N
- **Blocked**: M
- **Last Session**: <date> - <summary>

### Session Plan
| # | Task | Status |
|---|------|--------|
| 1 | <task> | in-progress |
| 2 | <task> | not-started |
| 3 | <task> | not-started |

### Current Task
**Target Feature**: F00X - <description>
**Approach**: <brief plan>
**Estimated Scope**: <small/medium/large>

### Risks/Dependencies
- <any concerns>
```

## After the Report

**Immediately proceed to implement the selected feature.** Do not ask "Ready to proceed?" or wait for confirmation. The user invoked this prompt to start a productive coding session, so begin working right away.
