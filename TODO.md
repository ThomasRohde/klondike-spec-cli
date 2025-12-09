# FeatureCategory limitations

klondike feature add "Per-feature Copilot launch helper with copy-to-clipboard" --category integration --priority 1 --criteria "Feature Details view includes Copilot Session panel" --criteria "Shows recommended klondike copilot start command template" --criteria "Includes feature ID and description in command comment" --criteria "Copy-to-clipboard button works correctly"
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "C:\Users\thoma\.local\bin\klondike.exe\__main__.py", line 10, in <module>
    sys.exit(main())
             ~~~~^^
  File "C:\Users\thoma\Projects\klondike-spec-cli\src\klondike_spec_cli\cli.py", line 2595, in main
    app.run()
    ~~~~~~~^^
  File "C:\Users\thoma\AppData\Roaming\uv\tools\klondike-spec-cli\Lib\site-packages\pith\app.py", line 159, in run
    self._run_internal(args)
    ~~~~~~~~~~~~~~~~~~^^^^^^
  File "C:\Users\thoma\AppData\Roaming\uv\tools\klondike-spec-cli\Lib\site-packages\pith\app.py", line 179, in _run_internal
    self._invoke_command(name, args[1:])
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "C:\Users\thoma\AppData\Roaming\uv\tools\klondike-spec-cli\Lib\site-packages\pith\app.py", line 280, in _invoke_command
    definition.callback(**final_kwargs)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "C:\Users\thoma\Projects\klondike-spec-cli\src\klondike_spec_cli\cli.py", line 454, in feature
    _feature_add(effective_description, category, priority, criteria, notes)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\thoma\Projects\klondike-spec-cli\src\klondike_spec_cli\cli.py", line 492, in _feature_add
    cat = FeatureCategory(category) if category else config.default_category
          ~~~~~~~~~~~~~~~^^^^^^^^^^
  File "C:\Users\thoma\AppData\Roaming\uv\python\cpython-3.13.1-windows-x86_64-none\Lib\enum.py", line 726, in __call__
    return cls.__new__(cls, value)
           ~~~~~~~~~~~^^^^^^^^^^^^
  File "C:\Users\thoma\AppData\Roaming\uv\python\cpython-3.13.1-windows-x86_64-none\Lib\enum.py", line 1199, in __new__
    raise ve_exc
ValueError: 'integration' is not a valid FeatureCategory

# YOLO mode swithc init --yolo

{
  // ⚠️ Full YOLO for tools (file edits, refactors, etc.)
  // On recent VS Code this is the canonical setting name:
  "chat.tools.global.autoApprove": true,

  // Legacy name kept for compatibility with older builds
  "chat.tools.autoApprove": true,

  // Let the agent run larger plans without constant continuation prompts
  "chat.agent.maxRequests": 300,

  // Terminal auto-approve is ON, but tightly controlled via rules below
  "chat.tools.terminal.enableAutoApprove": true,

  // Extra safety: block auto-approval when file writes are detected (experimental)
  "chat.tools.terminal.blockDetectedFileWrites": true,

  // Keep VS Code's default allow/block rules and layer ours on top
  "chat.tools.terminal.ignoreDefaultAutoApproveRules": false,

  // Command-level allow/deny list (regex patterns wrapped in /.../)
  "chat.tools.terminal.autoApprove": {
    // ===== SAFE ALLOW-LIST (auto-approved) =====

    // Basic navigation / inspection (read-only)
    "/^(ls|dir)\\b/": true,
    "/^pwd\\b/": true,

    // Git: safe read-only commands
    "/^git\\s+(status|diff|log|show|branch|remote)\\b/": true,

    // Node.js / npm / pnpm / Yarn: testing and linting only
    "/^npm\\s+(test|run\\s+lint|run\\s+build)\\b/": true,
    "/^pnpm\\s+(test|lint|build)\\b/": true,
    "/^yarn\\s+(test|lint|build)\\b/": true,

    // Python: test + static checks + read-only pip ops
    "/^pytest\\b/": true,
    "/^python\\s+-m\\s+pytest\\b/": true,
    "/^black\\s+--check\\b/": true,
    "/^flake8\\b/": true,
    "/^mypy\\b/": true,
    "/^isort\\s+--check-only\\b/": true,
    "/^pip\\s+(list|check|show)\\b/": true,

    // Java / Maven / Gradle: tests/checks only
    "/^mvn\\s+(test|clean\\s+test|verify)\\b/": true,
    "/^gradle\\s+(test|check|build\\s+--dry-run)\\b/": true,

    // Go: testing and vetting
    "/^go\\s+(test|fmt|vet)\\b/": true,

    // Rust: testing and checking
    "/^cargo\\s+(test|check|fmt)\\b/": true,

    // Docker: safe inspection/build (no run/exec here)
    "/^docker\\s+(ps|images|build|logs)\\b/": true,

    // ===== DENY-LIST (NEVER auto-approved, always ask) =====

    // Generic destructive commands
    "rm": false,
    "rmdir": false,
    "del": false,
    "mv": false,
    "cp": false,
    "dd": false,
    "kill": false,
    "chmod": false,
    "chown": false,
    "sudo": false,

    // Package managers: installs / upgrades / global changes
    "/^pip3?\\s+install\\b/": false,
    "/^python\\s+-m\\s+pip\\s+install\\b/": false,
    "/^npm\\s+install\\b/": false,
    "/^pnpm\\s+install\\b/": false,
    "/^yarn\\s+(add|global\\s+add)\\b/": false,
    "/^uv\\s+pip\\b/": false,
    "/^uv\\s+tool\\b/": false,

    // Git mutations
    "/^git\\s+(push|reset|revert|clean|rm)\\b/": false,
    "/^git\\s+checkout\\s+-f\\b/": false,

    // Docker / containers runtime risks
    "/^docker\\s+(run|exec|rm|compose)\\b/": false,
    "/^podman\\s+(run|exec|rm)\\b/": false,

    // Network / data exfiltration helpers
    "curl": false,
    "wget": false,
    "Invoke-RestMethod": false,
    "Invoke-WebRequest": false,

    // PowerShell: deletion and process control
    "Remove-Item": false,
    "Remove-ItemProperty": false,
    "rip": false,
    "ri": false,
    "rd": false,
    "erase": false,

    "Stop-Process": false,
    "sp": false,
    "spps": false,
    "taskkill": false,

    // PowerShell process start / privilege escalation
    "Start-Process": false,
    "Start-Process -Verb RunAs": false,
    "saps": false,

    // Permissions / ACL changes
    "Set-Acl": false,
    "icacls": false,

    // Shutdown / restart
    "Stop-Computer": false,
    "Restart-Computer": false,
    "shutdown": false,

    // PowerShell eval-style execution
    "Invoke-Expression": false
  }
}

# Klondike version
