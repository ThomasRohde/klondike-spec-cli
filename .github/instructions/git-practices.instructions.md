---
description: "Git practices for long-running agent workflows"
applyTo: "**/*"
---

# Git Practices for Long-Running Agents

Effective git usage is critical for agent workflows. Git provides the safety net for reverting bad changes and the history that helps agents understand context.

## Commit Frequency

### DO: Commit Early and Often

- After completing a logical unit of work
- Before starting a risky change
- At natural stopping points
- Before ending a session

### DON'T: Batch All Changes

- Don't wait until "it's perfect"
- Don't combine unrelated changes
- Don't leave uncommitted changes at session end

## Commit Messages

Use conventional commit format:

```
<type>(<scope>): <short description>

<longer description if needed>

<footer with issues/breaking changes>
```

### Types

| Type | Use For |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change (no new feature or fix) |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `chore` | Maintenance, dependencies |
| `style` | Formatting (no code change) |

### Examples

```
feat(auth): add login form with email/password validation

Implements F003 acceptance criteria:
- Email format validation
- Password minimum length check
- Error message display

Closes #12
```

```
fix(api): handle null user in getProfile endpoint

Previously threw uncaught exception when user was not found.
Now returns 404 with appropriate error message.
```

## Recovery Patterns

### Revert a Bad Commit

```bash
# See recent commits
git log --oneline -10

# Revert a specific commit (creates new commit)
git revert <commit-hash>

# Or reset to before the commit (destructive)
git reset --hard <commit-hash>
```

### Recover Lost Work

```bash
# See all recent actions
git reflog

# Restore to a previous state
git reset --hard <reflog-entry>
```

### Stash Work in Progress

```bash
# Save current changes
git stash save "WIP: feature description"

# List stashes
git stash list

# Restore
git stash pop
```

## Branching

For larger features:

```bash
# Create feature branch
git checkout -b feature/F003-user-login

# Work, commit, work, commit...

# When complete, merge back
git checkout main
git merge feature/F003-user-login

# Clean up
git branch -d feature/F003-user-login
```

## Session End Checklist

Before ending any session:

1. [ ] `git status` shows nothing to commit
2. [ ] All changes have descriptive commit messages
3. [ ] Feature branch merged if applicable
4. [ ] Tags added for milestones

## Tags for Milestones

```bash
# Tag stable checkpoints
git tag -a v0.1.0 -m "MVP: basic functionality complete"
git tag -a checkpoint-auth-complete -m "Authentication features done"

# List tags
git tag -l
```

## What to Never Commit

- Secrets, API keys, passwords
- `.env` files with real credentials
- `node_modules` or other dependency folders
- Build artifacts
- Personal IDE settings (unless shared)
- Large binary files

Ensure `.gitignore` is properly configured.
