"""Shell completion support for klondike CLI.

Generates completion scripts for Bash, Zsh, and PowerShell.
"""

from __future__ import annotations

from pathlib import Path

# Available commands and their subactions
COMMANDS = {
    "init": {"options": ["--force", "-f"]},
    "status": {"options": ["--json"]},
    "feature": {
        "subactions": ["add", "list", "start", "verify", "block", "show", "edit"],
        "options": [
            "--description",
            "-d",
            "--category",
            "-c",
            "--priority",
            "-p",
            "--criteria",
            "--add-criteria",
            "--evidence",
            "-e",
            "--reason",
            "-r",
            "--status",
            "-s",
            "--json",
            "--notes",
        ],
    },
    "session": {
        "subactions": ["start", "end"],
        "options": [
            "--focus",
            "-f",
            "--summary",
            "-s",
            "--completed",
            "-c",
            "--blockers",
            "-b",
            "--next",
            "-n",
            "--auto-commit",
        ],
    },
    "validate": {"options": []},
    "progress": {"options": []},
    "report": {
        "options": [
            "--format",
            "--output",
            "-o",
            "--include-completed",
            "--include-blocked",
        ],
    },
    "import-features": {
        "options": ["--dry-run"],
    },
    "export-features": {
        "options": ["--status", "-s"],
    },
    "help": {"options": []},
}

BASH_COMPLETION_TEMPLATE = """# Bash completion for klondike
# Add to ~/.bashrc or ~/.bash_completion

_klondike_completion() {
    local cur prev words cword
    _init_completion || return

    local commands="init status feature session validate progress report import-features export-features help"
    local feature_actions="add list start verify block show edit"
    local session_actions="start end"
    local categories="core infrastructure documentation testing"
    local statuses="not-started in-progress verified blocked"

    # Complete commands at first position
    if [[ $cword -eq 1 ]]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
        return
    fi

    # Get the command
    local cmd="${words[1]}"

    case "$cmd" in
        feature)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "$feature_actions" -- "$cur"))
                return
            fi
            # Feature ID completion for actions that need it
            local action="${words[2]}"
            if [[ "$action" =~ ^(start|verify|block|show|edit)$ ]] && [[ $cword -eq 3 ]]; then
                # Complete feature IDs from registry
                local ids=$(_klondike_feature_ids)
                COMPREPLY=($(compgen -W "$ids" -- "$cur"))
                return
            fi
            # Options
            case "$prev" in
                -c|--category)
                    COMPREPLY=($(compgen -W "$categories" -- "$cur"))
                    ;;
                -s|--status)
                    COMPREPLY=($(compgen -W "$statuses" -- "$cur"))
                    ;;
                -p|--priority)
                    COMPREPLY=($(compgen -W "1 2 3 4 5" -- "$cur"))
                    ;;
                *)
                    COMPREPLY=($(compgen -W "--description -d --category -c --priority -p --criteria --add-criteria --evidence -e --reason -r --status -s --json --notes" -- "$cur"))
                    ;;
            esac
            ;;
        session)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "$session_actions" -- "$cur"))
                return
            fi
            COMPREPLY=($(compgen -W "--focus -f --summary -s --completed -c --blockers -b --next -n --auto-commit" -- "$cur"))
            ;;
        status)
            COMPREPLY=($(compgen -W "--json" -- "$cur"))
            ;;
        report)
            case "$prev" in
                --format)
                    COMPREPLY=($(compgen -W "markdown plain json" -- "$cur"))
                    ;;
                -o|--output)
                    COMPREPLY=($(compgen -f -- "$cur"))
                    ;;
                *)
                    COMPREPLY=($(compgen -W "--format --output -o --include-completed --include-blocked" -- "$cur"))
                    ;;
            esac
            ;;
        import-features)
            if [[ $prev == "import-features" ]]; then
                COMPREPLY=($(compgen -f -X '!*.@(yaml|yml|json)' -- "$cur"))
            else
                COMPREPLY=($(compgen -W "--dry-run" -- "$cur"))
            fi
            ;;
        export-features)
            case "$prev" in
                -s|--status)
                    COMPREPLY=($(compgen -W "$statuses" -- "$cur"))
                    ;;
                export-features)
                    COMPREPLY=($(compgen -f -- "$cur"))
                    ;;
                *)
                    COMPREPLY=($(compgen -W "--status -s" -- "$cur"))
                    ;;
            esac
            ;;
        init)
            COMPREPLY=($(compgen -W "--force -f" -- "$cur"))
            ;;
    esac
}

_klondike_feature_ids() {
    # Get feature IDs from klondike, if available
    klondike feature list --json 2>/dev/null | grep -o '"id": *"F[0-9]\\{3,4\\}"' | grep -o 'F[0-9]\\{3,4\\}' 2>/dev/null || echo ""
}

complete -F _klondike_completion klondike
"""

ZSH_COMPLETION_TEMPLATE = """#compdef klondike

# Zsh completion for klondike
# Add to ~/.zsh/completions/_klondike and add directory to fpath

_klondike() {
    local -a commands feature_actions session_actions categories statuses

    commands=(
        'init:Initialize a new klondike project'
        'status:Show project status'
        'feature:Manage features'
        'session:Manage sessions'
        'validate:Validate artifact integrity'
        'progress:Regenerate progress markdown'
        'report:Generate status report'
        'import-features:Import features from file'
        'export-features:Export features to file'
        'help:Show help'
    )

    feature_actions=(
        'add:Add a new feature'
        'list:List all features'
        'start:Start working on a feature'
        'verify:Mark feature as verified'
        'block:Mark feature as blocked'
        'show:Show feature details'
        'edit:Edit feature metadata'
    )

    session_actions=(
        'start:Start a new session'
        'end:End current session'
    )

    categories=(core infrastructure documentation testing)
    statuses=(not-started in-progress verified blocked)

    _arguments -C \\
        "1: :{_describe 'command' commands}" \\
        "*::arg:->args"

    case "$words[1]" in
        feature)
            _arguments -C \\
                "1: :{_describe 'action' feature_actions}" \\
                "*::arg:->feature_args"
            case "$words[1]" in
                start|verify|block|show|edit)
                    _klondike_feature_ids
                    ;;
                add)
                    _arguments \\
                        '--description[Feature description]:description:' \\
                        '-d[Feature description]:description:' \\
                        '--category[Category]:category:(${categories})' \\
                        '-c[Category]:category:(${categories})' \\
                        '--priority[Priority 1-5]:priority:(1 2 3 4 5)' \\
                        '-p[Priority 1-5]:priority:(1 2 3 4 5)' \\
                        '--criteria[Acceptance criteria]:criteria:'
                    ;;
            esac
            ;;
        session)
            _arguments -C \\
                "1: :{_describe 'action' session_actions}" \\
                '--focus[Session focus]:focus:' \\
                '-f[Session focus]:focus:' \\
                '--summary[Session summary]:summary:' \\
                '-s[Session summary]:summary:' \\
                '--completed[Completed items]:completed:' \\
                '-c[Completed items]:completed:' \\
                '--auto-commit[Auto-commit changes]'
            ;;
        status)
            _arguments '--json[Output as JSON]'
            ;;
        report)
            _arguments \\
                '--format[Output format]:format:(markdown plain json)' \\
                '--output[Output file]:output:_files' \\
                '-o[Output file]:output:_files' \\
                '--include-completed[Include completed features]' \\
                '--include-blocked[Include blocked features]'
            ;;
        import-features)
            _arguments \\
                '1:file:_files -g "*.{yaml,yml,json}"' \\
                '--dry-run[Preview without importing]'
            ;;
        export-features)
            _arguments \\
                '1:file:_files' \\
                '--status[Filter by status]:status:(${statuses})' \\
                '-s[Filter by status]:status:(${statuses})'
            ;;
        init)
            _arguments \\
                '--force[Force overwrite]' \\
                '-f[Force overwrite]'
            ;;
    esac
}

_klondike_feature_ids() {
    local -a ids
    ids=(${(f)"$(klondike feature list --json 2>/dev/null | grep -o '"id": *"F[0-9]\\{3,4\\}"' | grep -o 'F[0-9]\\{3,4\\}')"})
    _describe 'feature id' ids
}

_klondike "$@"
"""

POWERSHELL_COMPLETION_TEMPLATE = """# PowerShell completion for klondike
# Add to your PowerShell profile

$script:KlondikeCommands = @(
    'init', 'status', 'feature', 'session', 'validate',
    'progress', 'report', 'import-features', 'export-features', 'help'
)

$script:FeatureActions = @('add', 'list', 'start', 'verify', 'block', 'show', 'edit')
$script:SessionActions = @('start', 'end')
$script:Categories = @('core', 'infrastructure', 'documentation', 'testing')
$script:Statuses = @('not-started', 'in-progress', 'verified', 'blocked')

function Get-KlondikeFeatureIds {
    try {
        $json = klondike feature list --json 2>$null | ConvertFrom-Json
        return $json | ForEach-Object { $_.id }
    } catch {
        return @()
    }
}

Register-ArgumentCompleter -Native -CommandName klondike -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)

    $tokens = $commandAst.CommandElements
    $command = if ($tokens.Count -gt 1) { $tokens[1].Extent.Text } else { $null }
    $action = if ($tokens.Count -gt 2) { $tokens[2].Extent.Text } else { $null }

    # Complete commands
    if ($tokens.Count -le 2) {
        $script:KlondikeCommands | Where-Object { $_ -like "$wordToComplete*" } |
            ForEach-Object { [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_) }
        return
    }

    switch ($command) {
        'feature' {
            if ($tokens.Count -eq 3) {
                $script:FeatureActions | Where-Object { $_ -like "$wordToComplete*" } |
                    ForEach-Object { [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_) }
            } elseif ($action -in @('start', 'verify', 'block', 'show', 'edit') -and $tokens.Count -eq 4) {
                Get-KlondikeFeatureIds | Where-Object { $_ -like "$wordToComplete*" } |
                    ForEach-Object { [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_) }
            }
        }
        'session' {
            if ($tokens.Count -eq 3) {
                $script:SessionActions | Where-Object { $_ -like "$wordToComplete*" } |
                    ForEach-Object { [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_) }
            }
        }
    }

    # Complete options based on previous token
    $prevToken = $tokens[$tokens.Count - 2].Extent.Text
    switch ($prevToken) {
        { $_ -in @('-c', '--category') } {
            $script:Categories | Where-Object { $_ -like "$wordToComplete*" } |
                ForEach-Object { [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_) }
        }
        { $_ -in @('-s', '--status') } {
            $script:Statuses | Where-Object { $_ -like "$wordToComplete*" } |
                ForEach-Object { [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_) }
        }
        { $_ -in @('-p', '--priority') } {
            1..5 | Where-Object { "$_" -like "$wordToComplete*" } |
                ForEach-Object { [System.Management.Automation.CompletionResult]::new("$_", "$_", 'ParameterValue', "Priority $_") }
        }
        '--format' {
            @('markdown', 'plain', 'json') | Where-Object { $_ -like "$wordToComplete*" } |
                ForEach-Object { [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_) }
        }
    }
}

Write-Host "Klondike completions loaded. Type 'klondike <TAB>' to use."
"""


def generate_bash_completion() -> str:
    """Generate Bash completion script."""
    return BASH_COMPLETION_TEMPLATE


def generate_zsh_completion() -> str:
    """Generate Zsh completion script."""
    return ZSH_COMPLETION_TEMPLATE


def generate_powershell_completion() -> str:
    """Generate PowerShell completion script."""
    return POWERSHELL_COMPLETION_TEMPLATE


def save_completion_script(shell: str, output_path: Path | None = None) -> Path:
    """Save completion script to file.

    Args:
        shell: Shell type ('bash', 'zsh', 'powershell')
        output_path: Output path, defaults to appropriate location

    Returns:
        Path where script was saved

    Raises:
        ValueError: If shell type is not supported
    """
    generators = {
        "bash": (generate_bash_completion, "_klondike"),
        "zsh": (generate_zsh_completion, "_klondike"),
        "powershell": (generate_powershell_completion, "klondike.ps1"),
    }

    if shell not in generators:
        raise ValueError(f"Unsupported shell: {shell}. Use: bash, zsh, powershell")

    generator, default_name = generators[shell]
    content = generator()

    if output_path is None:
        output_path = Path.cwd() / default_name

    # Create parent directories if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    return output_path
