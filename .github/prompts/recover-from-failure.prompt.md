---
name: recover-from-failure
description: "Diagnose and recover from a broken project state"
---

# Goal

Diagnose why the project is broken and **recover to a clean, working state** before continuing with new feature work.

## Context

From Anthropic's research: agents often "spend substantial time trying to get the basic app working again" when left in broken states. This prompt provides a systematic approach to recovery.

## Instructions

### 1. Document Current Symptoms

Before making any changes:
- What error messages are you seeing?
- When did the project last work?
- What was the last change made?

```bash
# Check current state
git status
git log --oneline -10
git diff --stat
```

### 2. Identify Last Known Good State

```bash
# Find when tests last passed (if CI is configured)
git log --oneline --all | head -20

# Check for tags or stable commits
git tag -l

# Look at recent commit messages for clues
git log --oneline -20
```

### 3. Diagnostic Checklist

Run through common failure causes:

**Environment Issues:**
```bash
# Check dependencies are installed
# npm install / pip install -r requirements.txt / etc.

# Check for version mismatches
# node -v / python --version / etc.

# Check environment variables
# printenv | grep -i <relevant-vars>
```

**Build/Compile Issues:**
```bash
# Clear build caches
# rm -rf node_modules/.cache / __pycache__ / build / etc.

# Rebuild from scratch
# npm run build / cargo build / etc.
```

**Test Failures:**
```bash
# Run test suite with verbose output
# npm test -- --verbose / pytest -v / etc.
```

**Runtime Issues:**
```bash
# Check if processes are already running
# lsof -i :3000 / netstat -ano | findstr :3000

# Check logs
# tail -100 <log-file>
```

### 4. Triage and Recovery Strategy

Based on diagnosis, choose approach:

**Option A: Quick Fix**
If the issue is minor and clearly understood:
1. Fix the specific issue
2. Verify fix works
3. Commit with clear message

**Option B: Partial Revert**
If recent commits introduced the problem:
```bash
# Revert specific commit(s)
git revert <commit-hash>

# Or reset to specific commit (careful!)
git reset --hard <commit-hash>
```

**Option C: Full Reset**
If state is too corrupted:
```bash
# Stash any work you want to keep
git stash

# Reset to last known good state
git reset --hard <last-good-commit>

# Cherry-pick good changes if any
git cherry-pick <good-commit-hash>
```

**Option D: Fresh Clone**
If local state is too broken:
```bash
# Clone fresh copy
cd ..
git clone <repo-url> <project>-recovery
cd <project>-recovery

# Copy over any untracked files needed
```

### 5. Verify Recovery

After recovery attempt:

```bash
# Clean install dependencies
rm -rf node_modules  # or equivalent
npm install  # or equivalent

# Run build
npm run build  # or equivalent

# Run tests
npm test  # or equivalent

# Start dev server
./init.sh

# Smoke test
# <verify basic functionality>
```

### 6. Document the Incident

Update `agent-progress.md`:

```markdown
### Recovery Session - <Date>

#### Problem Symptoms
- <What was broken>
- <Error messages observed>

#### Root Cause
- <What caused the failure>
- <How it was identified>

#### Recovery Steps Taken
1. <Step 1>
2. <Step 2>
3. <Step 3>

#### Prevention Recommendations
- <How to avoid this in future>

#### State After Recovery
- <Confirmation of working state>
- <What features are verified working>
```

### 7. Prevent Recurrence

Consider:
- Adding pre-commit hooks for validation
- Improving init script to catch issues early
- Adding health checks to CI
- Documenting gotchas in progress file

## Output Format

```markdown
## Recovery Report

**Date**: <timestamp>
**Time to Recovery**: <duration>

### Diagnosis

**Symptoms**:
- <symptom 1>
- <symptom 2>

**Root Cause**: <explanation>

**Last Working Commit**: <hash> - <message>

### Recovery Actions

| Step | Action | Result |
|------|--------|--------|
| 1 | <action> | ✅/❌ |
| 2 | <action> | ✅/❌ |

### Verification

- [x] Dependencies installed
- [x] Build succeeds
- [x] Tests pass
- [x] Dev server starts
- [x] Smoke test passes

### Prevention Measures

- <recommendation 1>
- <recommendation 2>

### Ready to Continue

**Status**: ✅ Recovered / ⚠️ Partial Recovery / ❌ Needs Escalation

**Next Steps**: <what to do now>
```
