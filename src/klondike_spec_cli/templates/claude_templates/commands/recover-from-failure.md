Diagnose and recover from a broken project state

# Goal

Systematically diagnose and recover from a broken or inconsistent project state.

## Instructions

### 1. Assess the Damage

```bash
# Check klondike artifact integrity
klondike validate

# Check git state
git status
git log --oneline -5

# Check for uncommitted changes
git diff --stat
```

### 2. Identify the Problem

**Common issues:**

| Symptom | Likely Cause | Fix Path |
|---------|--------------|----------|
| Failing tests | Code regression | Revert or fix |
| Build errors | Missing deps, syntax | Check recent changes |
| Artifact corruption | Manual edits | Restore from git |
| Merge conflicts | Concurrent work | Resolve conflicts |
| Missing files | Incomplete commit | Check stash/history |

### 3. Recovery Strategies

**For failing tests:**
```bash
# Find when tests last passed
git log --oneline | head -20
git bisect start HEAD <last-known-good>
git bisect run npm test  # or pytest, etc.
```

**For broken artifacts:**
```bash
# Restore klondike artifacts from last commit
git checkout HEAD -- .klondike/
klondike validate
```

**For messy git state:**
```bash
# Stash current work
git stash push -m "WIP: recovery"

# Reset to clean state
git checkout main
git pull origin main

# Create fresh branch
git checkout -b recovery-$(date +%Y%m%d)

# Cherry-pick good commits if needed
git cherry-pick <commit-hash>
```

### 4. Verify Recovery

```bash
# Run full validation suite
klondike validate

# Run tests
npm test  # or pytest, etc.

# Check build
npm run build  # if applicable
```

### 5. Document What Happened

```bash
klondike session start --focus "Recovery from <issue>"
# ... do recovery work ...
klondike session end \
  --summary "Recovered from <issue>. Root cause: <explanation>" \
  --next "Resume normal development"
```

## Prevention Tips

1. **Commit early, commit often** - Small commits are easier to bisect
2. **Always run tests before commit** - Catch issues immediately
3. **Don't manually edit .klondike/*.json** - Use CLI commands
4. **Keep branches short-lived** - Merge frequently to avoid drift
