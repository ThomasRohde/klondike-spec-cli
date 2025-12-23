"""Release command - automate version bumping and release tagging."""

import re
import subprocess
from pathlib import Path

from pith import PithException, echo

from ..git import (
    get_git_status,
    get_tags,
    git_add_all,
    git_commit,
    git_push,
    git_push_tag,
    git_tag,
)


def release_command(
    version: str | None = None,
    bump: str | None = None,
    message: str | None = None,
    dry_run: bool = False,
    push: bool = True,
    skip_tests: bool = False,
) -> None:
    """Automate version bumping and release tagging.

    Handles the complete release workflow: runs tests, bumps version in
    pyproject.toml, commits, tags, and pushes to trigger CI/CD.
    """
    pyproject_path = Path.cwd() / "pyproject.toml"

    if not pyproject_path.exists():
        raise PithException("pyproject.toml not found in current directory")

    # Read current version
    content = pyproject_path.read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        raise PithException("Could not find version in pyproject.toml")

    current_version = match.group(1)

    # If no version or bump specified, show current version
    if not version and not bump:
        echo(f"📦 Current version: {current_version}")
        tags = get_tags()
        if tags:
            echo(f"📌 Latest tag: {tags[0]}")
        echo("")
        echo("Usage:")
        echo("  klondike release 0.3.0        # Release specific version")
        echo("  klondike release --bump patch # Bump patch (0.2.0 -> 0.2.1)")
        echo("  klondike release --bump minor # Bump minor (0.2.0 -> 0.3.0)")
        echo("  klondike release --bump major # Bump major (0.2.0 -> 1.0.0)")
        return

    # Calculate new version
    if bump:
        new_version = _bump_version(current_version, bump)
    elif version:
        new_version = version.lstrip("v")
    else:
        raise PithException("Either version or --bump must be specified")

    # Validate version format
    if not re.match(r"^\d+\.\d+\.\d+$", new_version):
        raise PithException(
            f"Invalid version format: {new_version}. Expected X.Y.Z (e.g., 0.3.0)"
        )

    tag_name = f"v{new_version}"
    release_msg = message or f"Release {tag_name}"

    echo("📋 Release Plan")
    echo("=" * 40)
    echo(f"  Current version: {current_version}")
    echo(f"  New version:     {new_version}")
    echo(f"  Tag:             {tag_name}")
    echo(f"  Message:         {release_msg}")
    echo("")

    if dry_run:
        echo("⚠️  DRY RUN - No changes will be made")
        echo("")
        echo("Steps that would be performed:")
        echo("  1. Update version in pyproject.toml")
        if not skip_tests:
            echo("  2. Run tests")
        echo(f"  {'3' if not skip_tests else '2'}. Commit version bump")
        if push:
            echo(f"  {'4' if not skip_tests else '3'}. Push commit to remote")
        echo(f"  {'5' if not skip_tests else '4'}. Create tag {tag_name}")
        if push:
            echo(f"  {'6' if not skip_tests else '5'}. Push tag to remote")
        echo("")
        echo("After completion:")
        echo("  - TestPyPI: Automatic (triggered by tag push)")
        echo("  - PyPI: Create GitHub Release from tag")
        return

    # Check for uncommitted changes
    status = get_git_status()
    if status.has_uncommitted_changes:
        raise PithException(
            "Working directory has uncommitted changes. Please commit or stash them first."
        )

    # Run tests unless skipped
    if not skip_tests:
        echo("🧪 Running tests...")
        try:
            result = subprocess.run(
                ["uv", "run", "pytest", "-q"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                echo("❌ Tests failed:")
                echo(result.stdout)
                echo(result.stderr)
                raise PithException("Tests must pass before release")
            echo("✅ Tests passed")
        except FileNotFoundError:
            # Try with pytest directly
            result = subprocess.run(
                ["pytest", "-q"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                raise PithException("Tests must pass before release") from None
            echo("✅ Tests passed")
        except subprocess.TimeoutExpired as err:
            raise PithException("Tests timed out") from err

    # Update version in pyproject.toml
    echo(f"📝 Updating version to {new_version}...")
    new_content = re.sub(
        r'^(version\s*=\s*")[^"]+(")',
        f"\\g<1>{new_version}\\g<2>",
        content,
        flags=re.MULTILINE,
    )
    pyproject_path.write_text(new_content)

    # Stage and commit
    echo("📦 Committing version bump...")
    git_add_all()
    commit_success, output = git_commit(f"chore: bump version to {new_version}")
    if not commit_success:
        # Restore original content on failure
        pyproject_path.write_text(content)
        raise PithException(f"Failed to commit: {output}")
    echo(f"✅ Committed: chore: bump version to {new_version}")

    # Push commit if requested
    if push:
        echo("⬆️  Pushing commit...")
        push_success, output = git_push()
        if not push_success:
            raise PithException(f"Failed to push: {output}")
        echo("✅ Pushed commit")

    # Create tag
    echo(f"🏷️  Creating tag {tag_name}...")
    tag_success, output = git_tag(tag_name, release_msg)
    if not tag_success:
        raise PithException(f"Failed to create tag: {output}")
    echo(f"✅ Created tag {tag_name}")

    # Push tag if requested
    if push:
        echo(f"⬆️  Pushing tag {tag_name}...")
        push_tag_success, output = git_push_tag(tag_name)
        if not push_tag_success:
            raise PithException(f"Failed to push tag: {output}")
        echo("✅ Pushed tag")

    echo("")
    echo(f"🎉 Released {tag_name}!")
    echo("")
    echo("Next steps:")
    echo("  📦 TestPyPI: Publishing automatically (triggered by tag)")
    echo("  📦 PyPI: Create a GitHub Release from the tag:")
    echo(
        f"     https://github.com/ThomasRohde/klondike-spec-cli/releases/new?tag={tag_name}"
    )


def _bump_version(version: str, bump_type: str) -> str:
    """Bump a semantic version.

    Args:
        version: Current version (e.g., "0.2.0")
        bump_type: Type of bump: "major", "minor", or "patch"

    Returns:
        New version string
    """
    parts = version.split(".")
    if len(parts) != 3:
        raise PithException(f"Invalid version format: {version}")

    try:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError as err:
        raise PithException(f"Invalid version format: {version}") from err

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise PithException(
            f"Invalid bump type: {bump_type}. Use major, minor, or patch"
        )
