Implement a feature in an isolated git worktree

# Goal

**Implement the assigned feature completely.** Do NOT wait for confirmation or permission.

You are working in an isolated git worktree - a safe sandbox where you can make bold changes without affecting the main project.

## Your Mission

The feature details should be provided by the user or via worktree context. Your job is to:

1. Complete a quick environment check (30 seconds max)
2. Implement ALL acceptance criteria for the feature
3. Test your implementation
4. Commit with a descriptive message

**Do not stop after the environment check. Proceed immediately to implementation.**

---

## Quick Environment Check (Do This First)

```bash
# Verify you're in the worktree
pwd
git branch --show-current

# Check project status (brief)
klondike status
```

> Spend no more than 30 seconds on orientation. Then start coding.

---

## Implementation Guidelines

### Work Freely

**Isolation**: You're on a dedicated branch in a separate directory
**Safe commits**: Nothing affects main until explicitly merged

- **Commit often** - Even incomplete work. It's YOUR branch.
- **Experiment** - Try risky refactors. The main project is safe.
- **Break things** - If it goes wrong, the worktree can be deleted.

### Commit Workflow

```bash
# Work-in-progress commits are fine
git add -A && git commit -m "wip: <description>"

# Final commit should be descriptive
git add -A && git commit -m "feat(F00X): <summary>

- Implemented <details>
- Added tests for <coverage>
- Meets all acceptance criteria"
```

### Before You Finish

1. **All acceptance criteria are met**
2. **Code compiles/lints** - Run the project's lint/build commands
3. **Tests pass** - if applicable
4. **Final commit** with descriptive message

---

## Session Rules

- Do NOT push to remote without explicit permission
- Do NOT modify the main project directory directly
- Do NOT wait for human confirmation - you are in autonomous mode

---

## CRITICAL: Do Not Wait

**You are in autonomous mode.** There is no human to confirm anything.

After the quick environment check, proceed IMMEDIATELY to implementing the feature. Do not ask for permission. Do not wait. Just implement.

## Feature Context

If running via `klondike copilot start -w --feature F00X`, the feature details will be injected below. Otherwise, ask the user which feature to implement.
