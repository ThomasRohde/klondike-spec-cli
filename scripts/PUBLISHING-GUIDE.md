# Klondike Publishing Guide

## Quick Start

```powershell
# Patch release (1.0.5 -> 1.0.6)
.\scripts\publish.ps1 -Bump patch

# Minor release (1.0.5 -> 1.1.0)
.\scripts\publish.ps1 -Bump minor

# Major release (1.0.5 -> 2.0.0)
.\scripts\publish.ps1 -Bump major
```

## What the Script Does

1. **Checks git status** - Ensures working directory is clean
2. **Runs tests** - Validates code with `pytest`
3. **Builds web frontend** - Compiles React app in `klondike-web/`
4. **Commits changes** - Commits any build artifacts
5. **Creates and pushes tag** - Creates versioned git tag (e.g., `v1.0.6`)
6. **Triggers CI/CD** - GitHub Actions publishes to PyPI

## Common Issues & Recovery

### Issue: "Tag already exists"

**Symptoms:**
```
fatal: tag 'v1.0.5' already exists
❌ Failed to create tag
```

**Recovery Steps:**

```powershell
# 1. Check where the tag exists
git tag -l v1.0.5          # Check locally
git ls-remote --tags origin v1.0.5  # Check remote

# 2. Delete the tag (if safe to do so)
git tag -d v1.0.5          # Delete locally
git push origin :refs/tags/v1.0.5   # Delete from remote

# 3. Re-run the publish script
.\scripts\publish.ps1 -Bump patch
```

**Note:** The improved script now automatically detects and offers to delete existing tags.

### Issue: "Tests failed"

**Symptoms:**
```
❌ Tests failed! Fix issues before releasing.
```

**Recovery:**
```powershell
# Fix the failing tests first
uv run pytest -v

# Skip tests if emergency hotfix (NOT RECOMMENDED)
.\scripts\publish.ps1 -Bump patch -SkipTests
```

### Issue: "Working directory not clean"

**Symptoms:**
```
Uncommitted changes detected:
M src/some_file.py
```

**Recovery:**
```powershell
# Option 1: Commit the changes
git add -A
git commit -m "fix: your changes"
.\scripts\publish.ps1 -Bump patch

# Option 2: Stash and release
git stash
.\scripts\publish.ps1 -Bump patch
git stash pop
```

### Issue: "Failed to push tag"

**Symptoms:**
```
error: failed to push some refs
```

**Recovery:**
```powershell
# 1. Check what happened
git log --oneline -5
git tag -l

# 2. If commits pushed but tag didn't:
git push origin v1.0.5

# 3. If nothing pushed, check network and retry
.\scripts\publish.ps1 -Bump patch
```

## Manual Recovery Process

If the script fails partway through:

### 1. Check Current State
```powershell
# What's the current version?
git describe --tags --abbrev=0

# What commits are unpushed?
git log origin/master..HEAD --oneline

# What tags exist?
git tag -l
```

### 2. Cleanup Partial Release

```powershell
# If tag was created locally but not pushed:
git tag -d v1.0.5

# If commits were made but not pushed:
git reset --soft HEAD~1  # Undo last commit but keep changes

# If tag was pushed but release failed:
# Just wait for GitHub Actions or manually trigger it
```

### 3. Start Fresh

```powershell
# Ensure clean state
git status
git fetch --all --tags

# Run publish script again
.\scripts\publish.ps1 -Bump patch
```

## Advanced Options

### Dry Run (Preview)
```powershell
# See what would happen without making changes
.\scripts\publish.ps1 -Bump patch -DryRun
```

### Custom Version
```powershell
# Release specific version
.\scripts\publish.ps1 -Version 2.0.0 -Message "Major release with breaking changes"
```

### Skip Steps (Emergency Use)
```powershell
# Skip tests (DANGEROUS)
.\scripts\publish.ps1 -Bump patch -SkipTests

# Skip web build (if no frontend changes)
.\scripts\publish.ps1 -Bump patch -SkipWebBuild
```

## Post-Release Verification

### 1. Check GitHub Actions
Visit: https://github.com/ThomasRohde/klondike-spec-cli/actions

Should see:
- ✅ Tests passed
- ✅ Build succeeded
- ✅ Published to PyPI

### 2. Verify on PyPI
Visit: https://pypi.org/project/klondike-spec-cli/

Should show new version within 5-10 minutes.

### 3. Test Installation
```powershell
# In a new terminal (without active venv)
uv tool upgrade klondike-spec-cli

# Verify version
klondike --version
# Should show: klondike-spec-cli v1.0.6
```

## Best Practices

1. **Always run tests first**: Don't use `-SkipTests` unless emergency
2. **Use dry run for unfamiliar releases**: Try `-DryRun` first
3. **Let commits accumulate**: No need to release after every commit
4. **Semantic versioning**:
   - `patch` (1.0.5 → 1.0.6): Bug fixes, no API changes
   - `minor` (1.0.5 → 1.1.0): New features, backward compatible
   - `major` (1.0.5 → 2.0.0): Breaking changes

## Troubleshooting Checklist

Before running the script, ensure:

- [ ] You're on the `master` branch
- [ ] Working directory is clean or changes are committed
- [ ] All tests pass locally (`uv run pytest -v`)
- [ ] You have push access to the repository
- [ ] You're connected to the internet

If stuck, check:
- Git tags: `git tag -l`
- Remote tags: `git ls-remote --tags origin`
- Unpushed commits: `git log origin/master..HEAD`
- GitHub Actions: https://github.com/ThomasRohde/klondike-spec-cli/actions

## Quick Reference Card

```powershell
# Most common command
.\scripts\publish.ps1 -Bump patch

# Recovery from tag conflict
git tag -d v1.0.5
git push origin :refs/tags/v1.0.5
.\scripts\publish.ps1 -Bump patch

# Emergency bypass (use sparingly!)
.\scripts\publish.ps1 -Bump patch -SkipTests

# Preview before doing
.\scripts\publish.ps1 -Bump patch -DryRun
```
