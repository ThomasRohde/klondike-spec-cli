---
name: recover-from-failure
description: "Diagnose and recover from a broken project state"
---

# Goal

Diagnose why the project is broken and **recover to a clean, working state** before continuing with new feature work.

## Instructions

### 1. Document Current Symptoms

Before making any changes:
- What error messages are you seeing?
- When did the project last work?
- What was the last change made?

```bash
git status
git log --oneline -10
git diff --stat
```

### 2. Identify Last Known Good State

```bash
# Find recent commits
git log --oneline -20

# Check for tags or stable commits
git tag -l
```

### 3. Diagnostic Checklist

**Environment Issues:**
```bash
# Check dependencies are installed
# npm install / pip install -r requirements.txt / etc.

# Check for version mismatches
# node -v / python --version / etc.
```

**Build/Compile Issues:**
```bash
# Clear build caches
# rm -rf node_modules/.cache / __pycache__ / build / etc.

# Rebuild from scratch
```

**Runtime Issues:**
```bash
# Check if processes are already running on target port
# lsof -i :3000 / netstat -ano | findstr :3000
```

### 4. Recovery Strategy

**Option A: Quick Fix**
If the issue is minor and clearly understood:
1. Fix the specific issue
2. Verify fix works
3. Commit with clear message

**Option B: Partial Revert**
```bash
git revert <commit-hash>
```

**Option C: Full Reset**
```bash
git stash
git reset --hard <last-good-commit>
```

### 5. Verify Recovery

```bash
# Clean install dependencies
# Run build
# Run tests
# Start dev server
./init.sh
```

### 6. Document the Incident

Update progress file with:
- Problem symptoms
- Root cause
- Recovery steps taken
- Prevention recommendations

## Output Format

```markdown
## Recovery Report

**Date**: <timestamp>
**Time to Recovery**: <duration>

### Diagnosis
**Symptoms**: <what was broken>
**Root Cause**: <explanation>
**Last Working Commit**: <hash>

### Recovery Actions
| Step | Action | Result |
|------|--------|--------|
| 1 | <action> | ✅/❌ |

### Verification
- [x] Dependencies installed
- [x] Build succeeds
- [x] Tests pass
- [x] Dev server starts

### Prevention Measures
- <recommendation>
```
