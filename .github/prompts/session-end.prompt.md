---
name: session-end
description: "End a coding session with proper documentation and clean state"
---

# Goal

Execute the **standardized shutdown routine** for a long-running agent session, ensuring the codebase is left in a clean, well-documented state for the next session.

## Context

This prompt implements the "clean state" requirement from Anthropic's long-running agent research. Every session must end with the environment in a state that:
- Is appropriate for merging to main branch
- Has no major bugs or half-implemented features
- Is well-documented with clear next steps
- Could be picked up by any developer (human or AI)

## Instructions

### 1. Verify Clean State

**Step 1: Detect stack and available commands**

Read `package.json` (or `pyproject.toml`, `Cargo.toml`, `go.mod`) to find:
- Build command (e.g., `scripts.build`)
- Test command (e.g., `scripts.test`)
- Lint command (e.g., `scripts.lint`)

**Step 2: Run and record each command**

```bash
# Check for uncommitted changes
git status

# Run detected commands (example for Node.js)
npm run build
npm run test
npm run lint
```

**Step 3: Record results before any commit**

```markdown
#### Pre-Commit Verification
| Command | Exit Code | Notes |
|---------|-----------|-------|
| npm run build | 0 | ✅ Build succeeded |
| npm test | 0 | ✅ 42/42 tests passed |
| npm run lint | 0 | ✅ No issues |
```

**If a command is missing:**
- Note in Technical Notes: "No lint script configured"
- Do NOT silently skip

**If there are failures:**
- Fix them before proceeding
- If unfixable, revert to last good state and document

### 2. Commit Outstanding Work

All changes should be committed with descriptive messages:

```bash
# Stage changes
git add -A

# Commit with conventional commit message
git commit -m "<type>(<scope>): <description>

<body explaining what and why>

<footer with any breaking changes or issues>"
```

Commit types:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code change that doesn't fix bug or add feature
- `docs`: Documentation only
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### 3. Verify Feature Completion

For any features you worked on:

1. **Run end-to-end verification** (not just unit tests)
2. **Test as a user would** - browser, CLI, actual API calls
3. **Capture evidence** - logs, screenshots, command output
4. **Only mark complete** if ALL acceptance criteria are met

Update `features.json`:
```json
{
  "status": "verified",
  "passes": true,
  "verifiedAt": "<ISO timestamp>",
  "verifiedBy": "agent-session-<date>",
  "evidenceLinks": [
    "test-results/F00X-screenshot.png",
    "test-results/F00X-console.log"
  ],
  "notes": "Tested in Chrome and Firefox, edge cases handled"
}
```

**Important**: If feature is incomplete, set `status: "in-progress"` and leave `passes: false` - it's okay!

### 4. Complete or Park Session Plan

**Every task from your session plan must be resolved:**

| Status | Action Required |
|--------|----------------|
| `done` | No action - task complete |
| `blocked` | Document: what's blocking, who/what can unblock, suggested next step |
| `in-progress` | Either finish it OR convert to `blocked` with handoff notes |
| `not-started` | Either complete it OR document why deferred |

**You may NOT end a session with tasks in `in-progress` or `not-started` without explicit handoff.**

### 5. Update Progress File

Append a new session entry to `agent-progress.md`:

```markdown
### Session X - <Date>
**Duration**: ~<time>
**Focus**: <feature ID and name>

#### Completed
- <Specific accomplishment 1>
- <Specific accomplishment 2>
- <Files changed: list key files>

#### Attempted But Incomplete
- <What was tried that didn't work>
- <Why it didn't work>

#### Blockers Discovered
- <Any issues that need resolution>
- <Missing dependencies or decisions needed>

#### Recommended Next Steps
1. <Most important next action>
2. <Second priority>
3. <Third priority>

#### Technical Notes
- <Any non-obvious decisions made>
- <Gotchas for next session>
- <Useful commands discovered>
```

### 6. Final Verification

```bash
# Ensure everything is committed
git status  # Should show "nothing to commit, working tree clean"

# Verify app still works
./init.sh && <smoke-test-command>
```

### 7. Summary Report

Provide a brief handoff summary.

## Output Format

```markdown
## Session End Report

**Session Duration**: <time>
**Commits Made**: <count>

### Pre-Commit Verification
| Command | Exit Code | Notes |
|---------|-----------|-------|
| npm run build | 0 | ✅ |
| npm test | 0 | ✅ X tests passed |
| npm run lint | 0 | ✅ |

### Session Plan Resolution
| # | Task | Final Status | Notes |
|---|------|--------------|-------|
| 1 | <task> | done | Completed |
| 2 | <task> | done | Completed |
| 3 | <task> | blocked | Needs API key - see notes |

### Accomplishments
| Feature | Status | Evidence |
|---------|--------|----------|
| F00X | ✅ verified | [screenshot](test-results/F00X.png) |
| F00Y | 🔄 in-progress | 80% done, needs E2E test |

### Files Changed
- `path/to/file1.ts` - <what changed>
- `path/to/file2.ts` - <what changed>

### State Verification
- [x] All changes committed
- [x] Pre-commit checks passed and recorded
- [x] Smoke test passing
- [x] Progress file updated
- [x] Features.json accurate (with evidence links)
- [x] Session plan resolved (no dangling tasks)

### Handoff to Next Session
> <2-3 sentence summary of where things stand and what to do next>

### Git Log (This Session)
\`\`\`
<output of git log showing this session's commits>
\`\`\`
```
