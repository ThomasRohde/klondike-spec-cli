<#
.SYNOPSIS
    Automates the complete Klondike publishing workflow.

.DESCRIPTION
    This script handles the full release process:
    1. Runs tests to ensure everything passes
    2. Builds the klondike-web frontend
    3. Builds the Python wheel with bundled assets
    4. Creates a git tag and pushes to trigger CI/CD
    5. GitHub Actions then publishes to PyPI

.PARAMETER Version
    The version to release (e.g., "1.0.1"). Either this or -Bump is required.

.PARAMETER Bump
    The type of version bump: "major", "minor", or "patch".

.PARAMETER Message
    Optional release message. Defaults to "Release vX.Y.Z".

.PARAMETER SkipTests
    Skip running tests (not recommended for production releases).

.PARAMETER SkipWebBuild
    Skip rebuilding the web frontend (use if no frontend changes).

.PARAMETER DryRun
    Show what would be done without making any changes.

.EXAMPLE
    .\scripts\publish.ps1 -Bump patch
    # Bumps patch version (0.2.0 -> 0.2.1) and publishes

.EXAMPLE
    .\scripts\publish.ps1 -Version 2.0.0 -Message "Major release with breaking changes"
    # Releases specific version with custom message

.EXAMPLE
    .\scripts\publish.ps1 -Bump minor -DryRun
    # Shows what would happen without making changes
#>

param(
    [string]$Version,
    [ValidateSet("major", "minor", "patch")]
    [string]$Bump,
    [string]$Message,
    [switch]$SkipTests,
    [switch]$SkipWebBuild,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

function Write-Step {
    param([string]$Step, [string]$Description)
    Write-Host "`n" -NoNewline
    Write-Host "[$Step] " -ForegroundColor Cyan -NoNewline
    Write-Host $Description -ForegroundColor White
    Write-Host ("=" * 60) -ForegroundColor DarkGray
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Get-CurrentVersion {
    $versionFile = Join-Path $ProjectRoot "src\klondike_spec_cli\_version.py"
    if (Test-Path $versionFile) {
        $content = Get-Content $versionFile -Raw
        if ($content -match "__version__\s*=\s*version\s*=\s*'([^']+)'") {
            $version = $matches[1]
            # Strip dev/post suffixes
            return $version -replace '\.(dev|post)\d+.*$', ''
        }
    }
    
    # Fallback to git tags
    $tag = git describe --tags --abbrev=0 2>$null
    if ($tag) {
        return $tag -replace '^v', ''
    }
    
    throw "Could not determine current version"
}

function Get-BumpedVersion {
    param([string]$Current, [string]$BumpType)
    
    $parts = $Current.Split('.')
    if ($parts.Count -ne 3) {
        throw "Invalid version format: $Current"
    }
    
    $major = [int]$parts[0]
    $minor = [int]$parts[1]
    $patch = [int]$parts[2]
    
    switch ($BumpType) {
        "major" { return "$($major + 1).0.0" }
        "minor" { return "$major.$($minor + 1).0" }
        "patch" { return "$major.$minor.$($patch + 1)" }
    }
}

# Validate parameters
if (-not $Version -and -not $Bump) {
    Write-Host "Klondike Publishing Script" -ForegroundColor Magenta
    Write-Host "=" * 40 -ForegroundColor DarkGray
    
    $currentVersion = Get-CurrentVersion
    Write-Host "Current version: $currentVersion"
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\publish.ps1 -Bump patch      # $currentVersion -> $(Get-BumpedVersion $currentVersion 'patch')"
    Write-Host "  .\publish.ps1 -Bump minor      # $currentVersion -> $(Get-BumpedVersion $currentVersion 'minor')"
    Write-Host "  .\publish.ps1 -Bump major      # $currentVersion -> $(Get-BumpedVersion $currentVersion 'major')"
    Write-Host "  .\publish.ps1 -Version X.Y.Z   # Release specific version"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -SkipTests      Skip running tests"
    Write-Host "  -SkipWebBuild   Skip rebuilding web frontend"
    Write-Host "  -DryRun         Show what would happen"
    Write-Host "  -Message        Custom release message"
    exit 0
}

# Change to project root
Push-Location $ProjectRoot
try {
    # Calculate new version
    $currentVersion = Get-CurrentVersion
    if ($Version) {
        $newVersion = $Version -replace '^v', ''
    }
    else {
        $newVersion = Get-BumpedVersion $currentVersion $Bump
    }
    
    # Validate version format
    if ($newVersion -notmatch '^\d+\.\d+\.\d+$') {
        throw "Invalid version format: $newVersion. Expected X.Y.Z"
    }
    
    $tagName = "v$newVersion"
    $releaseMessage = if ($Message) { $Message } else { "Release $tagName" }
    
    Write-Host "`n♠️  Klondike Publishing Script" -ForegroundColor Magenta
    Write-Host "=" * 60 -ForegroundColor DarkGray
    Write-Host "  Current version: $currentVersion"
    Write-Host "  New version:     $newVersion"
    Write-Host "  Tag:             $tagName"
    Write-Host "  Message:         $releaseMessage"
    if ($DryRun) {
        Write-Host ""
        Write-Warning "DRY RUN - No changes will be made"
    }
    Write-Host ""
    
    # Step 1: Check git status
    Write-Step "1/6" "Checking git status"
    $gitStatus = git status --porcelain
    if ($gitStatus) {
        Write-Host "Uncommitted changes detected:" -ForegroundColor Yellow
        Write-Host $gitStatus
        if (-not $DryRun) {
            $confirm = Read-Host "Commit all changes before release? (y/N)"
            if ($confirm -ne 'y') {
                throw "Aborted: Please commit or stash changes first"
            }
        }
    }
    else {
        Write-Success "Working directory is clean"
    }
    
    # Step 2: Run tests
    if (-not $SkipTests) {
        Write-Step "2/6" "Running tests"
        if ($DryRun) {
            Write-Host "Would run: uv run pytest -v"
        }
        else {
            $env:CI = "true"
            uv run pytest -v
            if ($LASTEXITCODE -ne 0) {
                throw "Tests failed! Fix issues before releasing."
            }
            Write-Success "All tests passed"
        }
    }
    else {
        Write-Step "2/6" "Skipping tests (--SkipTests)"
        Write-Warning "Tests skipped - not recommended for production!"
    }
    
    # Step 3: Build web frontend
    if (-not $SkipWebBuild) {
        Write-Step "3/6" "Building web frontend"
        if ($DryRun) {
            Write-Host "Would run: npm run build (in klondike-web)"
        }
        else {
            Push-Location (Join-Path $ProjectRoot "klondike-web")
            try {
                npm run build
                if ($LASTEXITCODE -ne 0) {
                    throw "Web build failed!"
                }
                Write-Success "Web frontend built successfully"
            }
            finally {
                Pop-Location
            }
        }
    }
    else {
        Write-Step "3/6" "Skipping web build (--SkipWebBuild)"
    }
    
    # Step 4: Commit any changes (including new web build)
    Write-Step "4/6" "Committing changes"
    $gitStatus = git status --porcelain
    if ($gitStatus) {
        if ($DryRun) {
            Write-Host "Would commit changes with message: 'chore: prepare release $newVersion'"
        }
        else {
            git add -A
            git commit -m "chore: prepare release $newVersion"
            Write-Success "Changes committed"
        }
    }
    else {
        Write-Success "No changes to commit"
    }
    
    # Step 5: Create and push tag
    Write-Step "5/6" "Creating release tag"
    if ($DryRun) {
        Write-Host "Would create tag: $tagName"
        Write-Host "Would push to origin"
    }
    else {
        # Check if tag already exists locally
        $localTagExists = git tag -l $tagName
        if ($localTagExists) {
            Write-Warning "Tag $tagName already exists locally"
            $confirm = Read-Host "Delete and recreate tag? (y/N)"
            if ($confirm -eq 'y') {
                git tag -d $tagName
                Write-Host "Deleted local tag $tagName"
            }
            else {
                throw "Tag $tagName already exists. Delete it manually with: git tag -d $tagName"
            }
        }
        
        # Check if tag exists remotely
        git fetch --tags 2>$null
        $remoteTagExists = git ls-remote --tags origin $tagName
        if ($remoteTagExists) {
            Write-Warning "Tag $tagName already exists on remote"
            $confirm = Read-Host "Delete remote tag and recreate? (y/N)"
            if ($confirm -eq 'y') {
                git push origin :refs/tags/$tagName
                Write-Host "Deleted remote tag $tagName"
            }
            else {
                throw "Tag $tagName already exists on remote. Delete it manually with: git push origin :refs/tags/$tagName"
            }
        }
        
        # Push commits first
        Write-Host "Pushing commits..."
        git push origin HEAD
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to push commits"
        }
        
        # Create annotated tag
        Write-Host "Creating tag $tagName..."
        git tag -a $tagName -m $releaseMessage
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create tag"
        }
        
        # Push tag
        Write-Host "Pushing tag..."
        git push origin $tagName
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to push tag"
        }
        Write-Success "Tag $tagName created and pushed"
    }
    
    # Step 6: Summary
    Write-Step "6/6" "Release complete!"
    
    if ($DryRun) {
        Write-Host ""
        Write-Warning "DRY RUN completed - no changes were made"
        Write-Host ""
        Write-Host "To perform the actual release, run without -DryRun"
    }
    else {
        Write-Host ""
        Write-Host "🎉 " -NoNewline
        Write-Host "Released $tagName!" -ForegroundColor Green
        Write-Host ""
        Write-Host "GitHub Actions will now:" -ForegroundColor Cyan
        Write-Host "  1. Run tests"
        Write-Host "  2. Build the package"
        Write-Host "  3. Publish to PyPI"
        Write-Host ""
        Write-Host "Monitor progress at:" -ForegroundColor Cyan
        Write-Host "  https://github.com/ThomasRohde/klondike-spec-cli/actions"
        Write-Host ""
        Write-Host "Once published, users can install/upgrade with:" -ForegroundColor Cyan
        Write-Host "  uv tool install klondike-spec-cli"
        Write-Host "  uv tool upgrade klondike-spec-cli"
    }
    
}
catch {
    Write-Host ""
    Write-Error $_.Exception.Message
    exit 1
}
finally {
    Pop-Location
}
