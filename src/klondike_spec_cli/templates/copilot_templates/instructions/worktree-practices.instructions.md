---
description: "Best practices for working in isolated git worktree sessions"
applyTo: "**/klondike-worktrees/**"
---

# Git Worktree Session Practices

When working in an isolated git worktree created by `klondike copilot start --worktree`, follow these practices to maximize the benefits of isolation while maintaining code quality.

## Understanding Your Environment

### You Are NOT in the Main Project

```
Main Project: C:\Users\you\Projects\my-project  (← Protected)
     ↓ git worktree add
Worktree:     C:\Users\you\klondike-worktrees\my-project\f001-abc123  (← You are here)
```

Changes you make here do NOT affect the main project until explicitly merged or applied.

### Your Branch

- Branch name follows pattern: `klondike/<feature-or-session>-<uuid>`
- It was created from the parent branch (usually `main` or `master`)
- You have full commit rights to this branch
- It exists only locally until you push

## Commit Practices in Worktrees

### DO: Commit Early and Often

In a worktree, commits are cheap and risk-free:

```bash
# Work-in-progress commits are fine
git commit -m "wip: exploring approach for auth"
git commit -m "wip: auth working, needs tests"
git commit -m "wip: tests added, cleaning up"
```

### DO: Use Descriptive Final Commits

Before session ends, squash or create a clean final commit:

```bash
# Option 1: Interactive rebase to clean up
git rebase -i HEAD~5  # Squash WIP commits

# Option 2: Just ensure last commit is descriptive
git commit -m "feat(F001): implement user authentication

- Login form with email/password validation
- Session management with JWT tokens
- Password reset flow
- All acceptance criteria met
- 15 tests added, all passing"
```

### DON'T: Push Without Permission

The worktree branch is local. Pushing creates remote state that persists beyond the session:

```bash
# ❌ Don't do this unless explicitly requested
git push origin klondike/f001-abc123
```

## Testing in Worktrees

### Run Full Test Suite

Before ending a worktree session, always run tests:

```bash
# Python projects
uv run pytest tests/ -v

# Node.js projects  
CI=true npm test
```

### Verify Lint/Format

```bash
# Python
uv run ruff check src tests
uv run ruff format --check src tests

# Node.js
npm run lint
npm run format:check
```

## Applying Changes to Main Project

### Option 1: Automatic (--apply flag)

If started with `klondike copilot start -w --apply`, changes are applied automatically via `git apply`.

### Option 2: Manual Merge

```bash
cd /path/to/main/project
git merge klondike/f001-abc123
```

### Option 3: Cherry-Pick

For selective changes:

```bash
cd /path/to/main/project
git cherry-pick <commit-hash>
```

### Option 4: Patch File

Create a patch for review:

```bash
# In worktree
git diff main > feature.patch

# In main project
git apply feature.patch
```

## Cleanup

### Automatic Cleanup

If started with `--cleanup` flag, worktree is removed when session ends.

### Manual Cleanup

```bash
klondike copilot cleanup  # Removes all worktrees for this project
```

Or manually:

```bash
cd /path/to/main/project
git worktree remove ~/klondike-worktrees/project/session-name
git branch -D klondike/session-name
```

## When Things Go Wrong

### Worktree is Broken

Just delete it and start fresh:

```bash
klondike copilot cleanup
klondike copilot start --worktree --feature F001
```

### Want to Abandon Changes

If you don't want to keep any changes:

```bash
# Just cleanup without applying
klondike copilot cleanup
```

The main project remains untouched.

### Need to Compare with Main

```bash
# See what's different
git diff main

# See commit history since fork
git log main..HEAD
```

## Benefits of Worktree Sessions

| Aspect | Normal Session | Worktree Session |
|--------|---------------|------------------|
| Commit risk | Affects main branch | Isolated branch |
| Rollback | Need git revert | Just delete worktree |
| Experimentation | Risky | Safe |
| Parallel work | Hard | Easy - multiple worktrees |
| Code review | Changes immediate | Can review before merge |
