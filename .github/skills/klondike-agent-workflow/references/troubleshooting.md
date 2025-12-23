# Klondike Troubleshooting

Common issues and recovery patterns for klondike-managed projects.

## Table of Contents

- [Common Errors](#common-errors)
- [Artifact Issues](#artifact-issues)
- [Git Issues](#git-issues)
- [Session Recovery](#session-recovery)
- [Feature State Issues](#feature-state-issues)
- [Worktree Problems](#worktree-problems)

---

## Common Errors

### "klondike: command not found" or wrong syntax errors

**Causes:**
- Using `--help` flag (klondike doesn't support this)
- Not in correct directory
- klondike not installed

**Fixes:**
```bash
# ✓ Correct usage
klondike                    # Shows all commands
klondike status             # Run command directly
klondike feature list       # Commands show usage on error

# ✗ Wrong
klondike --help             # Not supported
klondike feature --help     # Not supported
```

### "No .klondike directory found"

**Cause:** Not in a klondike project or wrong directory.

**Fix:**
```bash
# Check you're in the right place
pwd
ls -la  # Look for .klondike/

# If new project, initialize
klondike init
```

### "Invalid feature ID format"

**Cause:** Feature IDs must be F### format (e.g., F001, F042).

**Fix:**
```bash
# Correct format
klondike feature start F001  # ✓
klondike feature start 1     # ✗
klondike feature start f001  # ✗
```

### "Evidence is required for verification"

**Cause:** `feature verify` needs proof.

**Fix:**
```bash
# Provide evidence path(s)
klondike feature verify F001 --evidence "test-results/F001.png"
klondike feature verify F001 -e "log.txt,screenshot.png"
```

### "Feature not found: F0XX"

**Cause:** Feature ID doesn't exist in registry.

**Fix:**
```bash
# Check existing features
klondike feature list

# Use correct ID
klondike feature show F001
```

---

## Artifact Issues

### Metadata Mismatch

**Symptom:** `klondike validate` shows count mismatches.

```
❌ metadata.totalFeatures (5) != actual (7)
❌ metadata.passingFeatures (2) != actual (3)
```

**Fix:**
```bash
# Session start auto-fixes metadata
klondike session start --focus "Fix metadata"

# Or manually trigger save
klondike feature list  # Loads and can trigger save
```

### Corrupted features.json

**Symptom:** JSON parse errors, commands fail.

**Fix (minor corruption):**
```bash
# Export what we can
klondike export-features backup.yaml 2>/dev/null

# Reinitialize
klondike init --force  # Requires confirmation

# Re-import
klondike import-features backup.yaml
```

**Fix (major corruption):**
```bash
# Check git history
git log --oneline .klondike/features.json

# Restore from git
git checkout HEAD~1 -- .klondike/features.json

# Validate
klondike validate
```

### Duplicate Feature IDs

**Symptom:** Validate shows duplicates.

**Fix:** Manual JSON edit is required for duplicates.
```bash
# See the issue
klondike validate

# Backup first
cp .klondike/features.json .klondike/features.json.bak

# Edit to remove duplicate
# (This is one case where manual edit is necessary)
```

---

## Git Issues

### Uncommitted Changes at Session End

**Symptom:** Session end warns about uncommitted work.

**Fix:**
```bash
# Commit everything
git add -A
git commit -m "feat(scope): complete feature"

# Then end session
klondike session end --summary "..."
```

### Merge Conflicts in .klondike/

**Symptom:** Git conflicts in features.json or agent-progress.json.

**Fix:**
```bash
# Accept incoming (theirs) for agent-progress.json
# It's auto-generated anyway
git checkout --theirs .klondike/agent-progress.json

# For features.json, carefully merge
# Keep all features, resolve status conflicts

# Regenerate progress
klondike progress
```

### Accidentally Committed Broken State

**Fix (last commit):**
```bash
# Amend the commit
git add -A
git commit --amend
```

**Fix (earlier commit):**
```bash
# Revert the problematic commit
git revert <commit-hash>

# Or reset to before the issue (destructive)
git reset --hard <commit-hash>
```

### Finding Lost Work

```bash
# See all recent actions
git reflog

# Restore to a previous state
git reset --hard <reflog-entry>
```

---

## Session Recovery

### Forgot to End Previous Session

**Symptom:** Starting new session when one is "active".

**Solution:** Just start the new session. Each session start is independent.

```bash
klondike session start --focus "New focus"
# Previous session is implicitly ended
```

### Lost Context Mid-Session

**Solution:** Use klondike to recover:

```bash
# See what's in progress
klondike status

# See feature details
klondike feature list --status in-progress
klondike feature show F001

# Continue from there
```

### Need to Restart Everything

**Nuclear option:**
```bash
# Export features first
klondike export-features backup.yaml

# Force reinitialize
klondike init --force

# Re-import features
klondike import-features backup.yaml
```

---

## Feature State Issues

### Feature Stuck in Wrong State

**Wrong status:**
```bash
# Re-mark as needed
klondike feature start F001        # Back to in-progress
klondike feature block F001 -r "reason"  # Mark blocked
```

**Accidentally verified:**
```bash
# Start again removes verified status
klondike feature start F001
```

### Multiple Features In-Progress

**Symptom:** Warning about other in-progress features.

**Best practice:** Work on one at a time, but warnings are non-blocking.

```bash
# See all in-progress
klondike feature list --status in-progress

# Complete or block extras
klondike feature block F002 --reason "Pausing for F001"
```

### Missing Acceptance Criteria

**Add criteria to existing feature:**
```bash
klondike feature edit F001 --add-criteria "New criterion,Another one"
```

---

## Worktree Problems

### Worktree Won't Clean Up

**Cause:** Uncommitted changes in worktree.

**Fix:**
```bash
# List worktrees
klondike copilot list

# Force cleanup
klondike copilot cleanup --force
```

### Worktree Already Exists

**Cause:** Previous session didn't clean up.

**Fix:**
```bash
# List and clean
klondike copilot list
klondike copilot cleanup

# Then start fresh
klondike copilot start -w
```

### Can't Find Worktree

**Default location:**
```bash
# Windows
cd %USERPROFILE%\klondike-worktrees\<project-name>\

# macOS/Linux
cd ~/klondike-worktrees/<project-name>/

# List contents
ls -la
```

### Changes Not Applying

**When using `--apply`:**
```bash
# Make sure you're in the MAIN project directory
pwd  # Should be original project, not worktree

# Apply manually if needed
cd ~/klondike-worktrees/project/session-id/
git diff HEAD~n..HEAD > changes.patch
cd /path/to/main/project
git apply changes.patch
```

---

## Prevention Tips

### Always Start With Status

```bash
klondike status  # First command of every session
```

### Validate Regularly

```bash
klondike validate  # After any unusual operation
```

### Commit Frequently

```bash
# After each meaningful change
git add -A && git commit -m "..."
```

### End Sessions Properly

```bash
# Don't just close the terminal
klondike session end --summary "..." --next "..."
```

### Use Worktrees for Risky Work

```bash
# Experimental changes
klondike copilot start -w

# If it fails, just clean up
klondike copilot cleanup
```
