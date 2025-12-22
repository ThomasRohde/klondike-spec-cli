Product Requirements Document: Klondike Serve Command
Overview

Klondike Serve is a proposed new CLI command (klondike serve) that launches a local web server providing a rich, real-time web interface for visualizing and managing a Klondike project. Klondike Spec CLI currently stores all project state in local files (e.g. .klondike/features.json for the feature registry and .klondike/agent-progress.json for the progress log)
GitHub
, accessible via CLI commands. The Klondike Serve UI will surface this data in an intuitive dashboard, allowing users to monitor project progress, inspect specifications, and perform project operations through a browser instead of the command line. This interface will mirror the functionality of the CLI (feature tracking, status updates, session logs, etc.) in a user-friendly visual format, updating in real-time as the underlying project state changes. By simply running klondike serve (with no additional setup), users can view and control their project via http://localhost:<port> in a web browser, enabling quicker insight into spec progress, task statuses, and recent changes without digging through JSON files or console output. In short, Klondike Serve aims to bring the power of Klondike’s agent-driven workflow to a modern web dashboard for enhanced usability and clarity.

Goals

Visualize All Project Data – Provide comprehensive views of all information available via Klondike CLI: feature list and statuses, spec progress (completed vs pending features), task breakdowns (feature details, acceptance criteria), session logs, project metadata, and recent changes (e.g. recent Git commits)
GitHub
, all in one cohesive UI.

Interactive Project Management – Allow users to perform key actions through the interface: e.g. editing spec items (features), marking tasks/steps as in-progress or completed (approving or verifying steps), triggering validations or status checks, editing project metadata/configuration, and otherwise managing the project flow entirely via UI controls (no manual file edits or CLI commands needed for core tasks).

Real-Time Updates – Ensure the interface stays up-to-date with project state in real time. Changes to the project (whether made through the UI or via CLI/other processes) should be reflected immediately, using WebSockets or efficient polling to sync data without requiring manual page refreshes. The UI should feel live, e.g. showing live progress updates during a coding session or when new features are added
dev.to
.

Ease of Use – Deliver a beautiful, intuitive user experience that adheres to modern web design best practices. Users (including those less familiar with CLI tools) should find it easy to navigate and understand the project’s status and to make changes. Clear visual cues (colors, icons, charts) will convey status (e.g. feature states) at a glance, complementing the rich terminal output the CLI provides
GitHub
.

Zero-Config Deployment – Make running the UI as simple as possible: no configuration or external setup should be required. Running klondike serve in a Klondike project directory should immediately start the server and make the UI available locally. The tool will autodetect the project’s .klondike folder and use its data; if the command is run outside a project, it will guide the user to initialize a project first (no complex setup).

Maintain Single-User, Local Scope – Design for a single user on a local machine. Since this UI is for local development use, there is no need for authentication or multi-user support. The focus is on a personal dashboard for the project’s maintainer/developer, not a multi-user web app.

User Stories

Project Overview at a Glance: “As a developer, I want to open a dashboard that immediately shows my project’s overall status – how many features are completed, in progress, or blocked – so that I can quickly gauge progress and health.” The Dashboard should display overall spec progress (e.g. X of Y features verified, percentage complete) and any high-priority items or warnings (like blockers).

Browse and Edit Features: “As a project owner, I want to review all the features/tasks in my spec, and easily update their details or status through the UI.” In a Spec Explorer view, the user can scroll through or search the list of all features (with ID, description, category, priority, status, etc.), click on a feature to see full details, and edit fields (description, category, priority, acceptance criteria, notes) or change its status. This should be easier than manually editing JSON – e.g. editing a feature’s acceptance criteria via a form.

Mark Progress with Approvals: “As a user, I want to mark tasks or steps as completed or approved through the interface, so I can signal progress.” For example, when a feature’s work is done, the user can mark it Verified (and provide required evidence) via a button instead of running klondike feature verify on the command line
GitHub
. If a feature becomes blocked or is being started, those actions (Block, Start) are also one-click operations with minimal friction. The UI might also allow approving suggested “Next Steps” from the AI (e.g. turning a recommended next step into a new task or marking it as acknowledged).

Trigger Validation & Checks: “As a QA engineer, I want to trigger a validation of the project (like running tests or checking artifact integrity) and see the results in the UI.” The interface could provide a way to run or trigger the equivalent of klondike validate or refresh the status. For instance, a “Validate” or “Refresh Status” action might re-read all data and highlight any inconsistencies (e.g. a feature marked verified without evidence)
GitHub
. Even if actual test execution isn’t directly integrated, the UI should at least allow regenerating the progress log or updating the status view easily (e.g. if auto-regeneration is off).

View Activity Log (Sessions & Changes): “As a team member, I want to see a timeline of what has happened in the project – coding sessions, completed features, and recent commits – so I understand recent progress.” An Activity Log view will list recent sessions (from the progress log) with their summaries: which features were completed, what the focus was, any blockers, and recommended next steps. It will also show recent Git commits (e.g. last 5 commits) to surface code changes
GitHub
. This gives context on how the project has evolved recently, all in one place.

Configure Project Easily: “As a user, I want to update project settings (like default feature category or PRD link) without editing YAML, so that configuration is straightforward.” The UI will include a Config Editor where settings from .klondike/config.yaml can be viewed and modified in a safe manner. For example, the user can set or change the “Product Requirements Document (PRD) source link”, default priority for new features, etc., via form fields
GitHub
. This saves time compared to running multiple klondike config CLI commands or editing the YAML by hand.

No-Hassle Startup: “As a developer, I want to launch the UI with a single command and not worry about fiddling with servers, ports, or logins.” Running klondike serve should quickly spin up the local server and perhaps even open the default web browser to the app (or at least print a URL like Local server running at http://127.0.0.1:8000). There should be no need to configure ports or auth – the default should just work (e.g. using port 8000 or next available). This encourages frequent use of the UI during development.

Functional Requirements
1. Data Display and Visualization

Project Dashboard: The UI Dashboard view will summarize key project info. This includes the project name and version, overall feature progress (with a visual indicator like a progress bar or pie chart showing what percentage of features are verified vs pending)
GitHub
, and counts of features by status (e.g. how many not-started, in-progress, blocked, verified)
GitHub
. It should highlight any Current Status of the project (e.g. “In Progress” if a session is active, or last session ended) and show the top priority features that remain to be done (similar to the CLI’s “Next Priority Features” list)
GitHub
. Additionally, the dashboard will display a brief Git status (if the project is a git repo): e.g. current branch, whether there are uncommitted changes, and a list of recent commit messages
GitHub
. This gives a one-glance overview of both spec progress and code changes.

Spec Explorer (Feature List): The application will provide a Spec Explorer view listing all features in the project’s feature registry (sourced from .klondike/features.json). Each feature entry should show at least: its ID (e.g. F001), short description, status (with a color or icon, e.g. ⏳ for not started, 🔄 for in-progress, 🚫 for blocked, ✅ for verified), and perhaps category or priority. Users can filter or group this list by status or category (e.g. view only “blocked” features) for easier navigation
GitHub
GitHub
. Clicking on a feature in the list opens the Task Viewer (detailed view).

Task Viewer (Feature Details): The Task Viewer is a detailed panel or page for a selected feature. It will display the feature’s full description, category, priority, and acceptance criteria (which are often multiple checklist items). It also shows the feature’s current status and any metadata like last worked date or dependencies (if present). If the feature is verified, it should show verification evidence links (e.g. links to test result files or screenshots) and who verified it
GitHub
GitHub
. If the feature is blocked, the block reason is displayed
GitHub
. The Task Viewer allows the user to edit these details and take actions (see Interactions below). Essentially, it’s the UI equivalent of klondike feature show <ID> (displaying all feature info)
GitHub
.

Activity Log (Session & Change History): The UI will include an Activity Log view that surfaces the chronological history of work on the project. This is largely derived from the agent progress log (agent-progress.json and its rendered markdown). It should list sessions in order (session 1, 2, …), each showing the date, agent name (if applicable), and focus/summary
GitHub
GitHub
. Under each session entry, the log of Completed items, In Progress items, Blockers, and Recommended Next Steps should be displayed, exactly as recorded in the session (these mirror the content in agent-progress.md for that session)
GitHub
GitHub
. This gives users a narrative of what the AI agent (or developer) did each session. In addition, the Activity Log can list recent Git commits (with commit message and timestamp) to show code changes alongside the session entries (e.g. intermix commits by time, or simply provide a separate recent commits section). This combined log helps users track both spec progress and code changes over time.

Configuration View: The Config Editor section will display the current project configuration values (from .klondike/config.yaml) such as default category, default priority, etc., in a readable form. Each setting should have a label and description (the CLI’s config file includes comments describing each field
GitHub
GitHub
 which can inform the UI labels). For example: Default Category for new features: core, Auto-regenerate progress log: true, PRD Source URL: (link), etc. The values should be editable (see below), but even in read-only mode they inform the user of the project’s settings (which otherwise are hidden in a YAML).

2. Interactive Controls & Editing

Edit Features (Spec Editing): Users can create and modify features through the UI. There will be an “Add Feature” function (e.g. a button on Spec Explorer) allowing the user to input a new feature’s description, category, priority, and acceptance criteria. This corresponds to klondike feature add functionality in the CLI. Each existing feature can be edited via the Task Viewer: the UI should allow editing the description (if permissible; in CLI, description might be immutable after creation
GitHub
), category, priority, or adding new acceptance criteria or implementation notes (which map to the notes field)
GitHub
GitHub
. Changes made in the UI are sent to the backend API, which updates the features.json accordingly. All edits should validate input (e.g. priority must be an integer, required fields not empty).

Feature Status Changes: The UI will provide one-click actions to change a feature’s status, reflecting the typical workflow operations:

Start Work on a Feature: e.g. an “Mark as In Progress” button in the feature detail view. This sets the feature’s status to in-progress, similar to klondike feature start <ID>
GitHub
. If any other features are already in progress, the backend may return a warning (the CLI warns if multiple features are in progress)
GitHub
GitHub
 – the UI should surface such warnings (e.g. as a toast notification).

Block a Feature: a “Block” action that marks the feature as blocked (requiring the user to enter a reason). This corresponds to klondike feature block <ID> --reason ...
GitHub
. The UI should prompt for the reason text and include it when calling the API. After blocking, the feature’s status is updated and it should display the blocked_by reason in its details
GitHub
.

Verify/Approve a Feature: a “Verify” or “Mark as Done” button for features that are completed. Marking a feature verified should trigger a form to attach evidence (since Klondike requires evidence when verifying a feature)
GitHub
. For example, the user could enter a link or path to test results, or upload a file (if file upload is supported, it might just provide a path that gets recorded). The UI must ensure evidence is provided (the backend will reject a verify action with no evidence)
GitHub
. Once verified, the feature’s status changes to verified and it records the current time and a “verified by user” (in CLI, this might use a default like “coding-agent” or user’s name) in the metadata
GitHub
. The interface should visually distinguish verified features (e.g. a green checkmark icon).

Other Feature Actions: The CLI also has feature show (view details) and feature edit (edit notes/criteria) which are covered by the UI’s direct editing capabilities, and feature prompt (generate an AI prompt for the feature) which is more of an advanced action. Initially, the UI may not expose the prompt generation feature, as it’s a developer-facing tool, but this could be an extension (perhaps an “AI Help” button that triggers prompt generation – however, this is out of scope for the first version).

Project Status & Validation: The UI should provide a means to refresh or validate the project status. For example, a “Recalculate Progress” or “Validate” button on the Dashboard can call an API to perform artifact validation (akin to klondike validate and klondike progress commands). This would ensure that derived metrics (like total vs passing features) are in sync and regenerate the markdown log if needed
GitHub
GitHub
. In practice, because the backend updates these automatically on each change, this may simply re-fetch the latest data and update UI displays. If something is wrong (e.g. mismatched counts), the backend or UI can flag it. The Dashboard could also incorporate a refresh action for the Git status/commits to fetch the latest commit info if needed. Real-time updates (next bullet) may reduce the need for manual refresh in most cases.

Session Management: (Basic support, optional in initial release). The UI can expose controls to manage coding sessions if it fits the workflow:

A “Start Session” action (e.g. on the Dashboard or a dedicated Sessions view) that prompts for an optional focus (what the user/agent will work on) and then initiates a new session (calls session start)
GitHub
. This would update the progress log (adding a session entry with status “In Progress”) and the UI should reflect that a session is active (perhaps an indicator on the Dashboard “Session X in progress, focus: …”). The UI doesn’t run the AI agent itself, but starting a session is mainly a bookkeeping action that could be done via UI for completeness.

An “End Session” action when work is done, prompting the user to enter the session summary, list of completed items, blockers encountered, and next steps (these correspond to CLI session end --summary ... --completed ... --blockers ... --next ...)
GitHub
GitHub
. Submitting this will update the progress log (closing out the current session) and mark the project’s current status as “Session Ended”
GitHub
. The Activity Log UI would then immediately show the updated session entry with all the details the user provided. Optionally, the UI could also offer an “auto-commit” toggle for session end (as the CLI does) to automatically commit changes with a standard message
GitHub
, but this may be an advanced feature; at minimum, the UI should remind the user to commit their work if there are uncommitted changes when ending a session (mirroring the CLI’s git warning)
GitHub
.
If implementing session controls, ensure the UI clearly indicates if a session is currently active (perhaps a persistent banner “Session X (In Progress)”). If the user tries to navigate away or close the UI with an active session, maybe warn them if they haven’t ended it. This keeps the workflow consistent. (Session management can be deferred if it complicates the initial scope; it’s nice-to-have for completeness of managing “project flow through the UI,” but not strictly required to meet the core goals.)

Config Editing: In the Config Editor view, each configuration field should be editable via appropriate UI controls:

Text input for strings (e.g. verified_by, PRD source URL),

Dropdown or text for default_category (perhaps pre-populate with common categories like core, ui, etc., since the CLI defines some common ones
GitHub
),

Number input or slider for default_priority,

Checkbox for booleans like auto_regenerate_progress.
The UI will send updates to the backend (e.g. a PUT/PATCH request to update config), and the backend will persist them to config.yaml. The UI should validate inputs (e.g. priority as numeric 1-5) and perhaps prompt for confirmation on critical changes. No restart of the server should be required; changes take effect immediately. For example, if auto_regenerate_progress is turned off, the UI might then offer a manual “Regenerate Progress Log” button since auto-regeneration is disabled.
Non-goal: Multi-user or auth settings – since the app is local, there are no user accounts or roles to manage, and no need for toggling authentication (the serve command will not implement auth).

General Usability: All interactive actions should provide feedback to the user. For instance, after clicking “Verify Feature F001,” the UI might show a success message “Feature F001 marked as Verified ✅” or display an error if something went wrong (e.g. “Error: evidence is required for verification” which the backend returns if no evidence provided
GitHub
). Use modal dialogs or confirmation prompts for potentially destructive actions (like blocking a feature or editing important text), especially if data might be lost. The interface should prevent or warn on obviously incorrect actions (e.g. don’t allow “Mark as Verified” on an already verified feature unless re-verifying is intended, etc.).

3. Real-Time Behavior

WebSocket Live Updates: The backend server will utilize WebSockets (or Server-Sent Events as an alternative) to push updates to the UI in real time. Whenever project state changes – whether via UI actions or external events (like the user running a CLI command in parallel, or the AI agent making changes in the background) – the server should notify the front-end. For example, if an AI coding session (running outside the UI) modifies the features.json or agent-progress.json, the server can detect the file change and emit an update. The React frontend, using a WebSocket connection, will receive these events and update the corresponding React state, causing the UI to re-render with fresh data
dev.to
. This ensures that the progress bars, feature lists, and logs on screen are always current without manual refresh. Real-time streaming could also be used if, say, we wanted to show live log output from an AI agent, but initially the scope is just syncing state changes.

Polling Fallback: In case WebSockets are not available or for simplicity, the UI can fall back to polling the server periodically (e.g. every 5 seconds) for changes. However, WebSocket is preferred for efficiency and truly instant updates
dev.to
. The real-time mechanism should handle network hiccups gracefully (auto-reconnect WebSocket if dropped, etc.). Since this is a local app, network issues are minimal, but the implementation should still be robust.

Data Consistency: The backend will be the single source of truth, reading from and writing to the project files (.klondike directory). It must ensure atomic updates (e.g. when a feature status changes, update both features.json and agent-progress.json accordingly, just as the CLI does). The UI’s real-time updates should ideally be driven by these backend file operations finishing. For example, after a user marks a feature as verified, the server updates the JSON files and then emits an update event with the new feature data and progress counts. This guarantees the UI reflects the actual saved state. If two UI actions occur quickly (or an external edit and a UI action conflict), the server should handle synchronization (perhaps by locking or queueing file writes to avoid race conditions).

Performance Considerations: The real-time updates should be efficient. The data volumes are relatively small (features list, progress log), so pushing the full updated JSON on each change is fine. But we should ensure that heavy operations (like regenerating the entire progress markdown or reading many commits) are done off the main thread if needed to keep the server responsive. Given typical project sizes (tens of features, dozens of log entries), performance should remain snappy. The UI should update only the parts that changed (React will handle diffing), to avoid reloading the entire page unnecessarily.

4. Backend Server Requirements

Framework & Architecture: The klondike serve command will spawn a lightweight Python web server, likely built on FastAPI (preferred for its async support and easy WebSocket integration) or Flask (simple and widely understood) for the HTTP API endpoints. FastAPI is a strong choice due to its performance and built-in support for WebSocket endpoints (useful for real-time)
dev.to
. The server will run locally (binding to localhost by default) and on a default port (e.g. 8000). It should not require root/admin privileges – if port 8000 is in use, it can either choose the next available port or allow the user to specify a port via an option (klondike serve --port 9000).

API Endpoints: The backend must provide a set of HTTP API endpoints that the React frontend can call to get or modify data. All data available via CLI or the internal MCP server should be exposed. At a high level, the API will include:

GET /api/status – Returns an overview of project status, including project name, version, summary of progress (total features, how many passing/verified, percentage complete) and feature counts by status
GitHub
GitHub
. It also returns info about the current or last session (if any) and the top priority features (this mirrors what klondike status and get_status provide)
GitHub
GitHub
. This is used to populate the Dashboard.

GET /api/features – Returns the full list of features (the entire feature registry) in JSON form. Each feature entry includes its ID, description, category, priority, status, passes (boolean if tests pass), and other metadata (acceptance criteria, dependencies, etc.)
GitHub
GitHub
. This powers the Spec Explorer list. Support query params for filtering (e.g. ?status=blocked to get only blocked features) similar to CLI filters
GitHub
.

POST /api/features – Create a new feature. The request body would include at least a description, and optionally category, priority, and acceptance criteria. The server will assign the next feature ID (e.g. F00X) and add it to the registry. Respond with the created feature data or an error if invalid.

GET /api/features/{id} – Get detailed info for a single feature {id}. This returns all fields for that feature (description, criteria list, notes, status, etc., potentially directly read from features.json or via the internal model). This could be used when navigating to the Task Viewer for a specific feature. (If the GET all features already provides everything, this may be optional – but it can be useful to avoid sending large acceptance criteria lists for all features at once, etc.)

PUT/PATCH /api/features/{id} – Update an existing feature’s properties. The client can send any editable fields (description, category, priority, acceptance criteria, notes). The server will apply the changes to the feature and save the updated registry. If certain fields are not allowed to change (e.g. maybe ID or description if immutable), the server will ignore or reject those changes.

POST /api/features/{id}/start – Mark feature {id} as in-progress. This sets the feature’s status to “in-progress” and updates its last_worked_on timestamp
GitHub
. The server might also update the progress log’s quick reference to reflect this change (e.g. updating priority features)
GitHub
. Returns success or error (e.g. if feature not found).

POST /api/features/{id}/block – Mark feature {id} as blocked with a given reason. The request should include a reason message. The server sets the feature’s status to “blocked” and stores the reason (in the feature’s blocked_by field)
GitHub
GitHub
. Save changes and return confirmation.

POST /api/features/{id}/verify – Mark feature {id} as verified. The request must include evidence (one or more evidence file paths or notes). The server will validate that evidence is provided (return error if not)
GitHub
, then update the feature: set status to “verified”, passes=true, record verified_at timestamp and verified_by (could use a default like “UI user” or the value from config e.g. “coding-agent” if not interactive)
GitHub
, and save the evidence links
GitHub
. It will also update the feature registry metadata counts (total/passing) and refresh any derived files (progress log). Respond with success or any validation error (e.g. missing evidence).

GET /api/progress – Retrieve the progress log (all sessions). The response will include the list of session entries (session number, date, agent, focus, completed items, blockers, next_steps, technical_notes) as well as any high-level summary (current_status, project start date, etc.)
GitHub
GitHub
. This powers the Activity Log view. If needed, support filtering (e.g. only last N sessions), though not critical since logs are usually not huge.

POST /api/session/start – Start a new session. This will create a new session entry in the progress log with status “(in progress)” and focus as provided
GitHub
GitHub
. It will also possibly perform the artifact validation (like the CLI does on session start) to ensure feature counts are consistent
GitHub
GitHub
; any warnings from validation can be returned (and shown to user). The response confirms the session started (session number, etc.). The server should also set an internal flag or state that a session is active.

POST /api/session/end – End the current session. The request would carry the summary/focus, completed items, blockers, and next_steps (all optional text fields) from the user input. The server populates the latest session entry with these details, marks its duration (could calculate or just mark ended), and sets the overall current_status to “Session Ended”
GitHub
. It should update quick references (like recommended next steps list, which CLI auto-generates if none provided
GitHub
). Also, it will run a git status check and optionally commit if an auto_commit flag was sent (if we support that)
GitHub
GitHub
. The response confirms session ended or errors if no active session was found. After this, the UI’s Activity Log will show the completed session info.

GET /api/config – Get current configuration settings. Returns all the config fields (default_category, default_priority, etc., as in the Config model)
GitHub
, perhaps along with the project’s Klondike CLI version and configured_agents list.

PUT /api/config – Update configuration. Accepts one or more config fields in the request body (e.g. {"default_category": "ui", "auto_regenerate_progress": false}) and writes them to the config. The server should validate values (e.g. known agent names, proper data types) and then save to .klondike/config.yaml (preserving any comments if possible, though likely it will rewrite the file in the standard format). Respond with the updated config or an error message if invalid. Changing config may influence other behavior (for example, if auto_regenerate_progress is turned off, the server might stop auto-updating the markdown log until manually triggered). The UI should be aware of such changes (it can refresh relevant parts of UI or inform the user).

GET /api/commits – (Optional) Retrieve recent Git commits. Since the status endpoint may already include recent commits
GitHub
, a separate endpoint might not be needed. But if we want a dedicated feed (e.g. for an extended activity log or to fetch more than 5 commits), we can have this endpoint return a list of commit messages (with authors, timestamps, etc.) by calling git log internally. This is a nice-to-have for an enriched Activity Log.

All endpoints will return JSON data. Errors will be returned with appropriate HTTP status codes and error messages in the response body. The API design should follow REST principles with clear resource names and use HTTP methods semantically (GET for read, POST for create/actions, PUT/PATCH for updates, etc.). Authentication is not required (the server is local), and CORS can be restricted to localhost for safety.

Server-UI Static Content: The backend will also need to serve the static files for the React frontend. When klondike serve runs, it can either bundle a pre-built single-page app (as part of the Python package) or dynamically serve a development build. For production, we will likely bundle the React app into the Python package (e.g. as files in a static/ directory). The FastAPI/Flask app will have a route to serve index.html and the JS/CSS assets. Hitting the root URL (e.g. http://localhost:8000/) should return the main HTML of the app. All API routes will likely be under a prefix (e.g. /api/…) to distinguish them from front-end routes. We should also support client-side routing (the app might use React Router), meaning the server’s index.html should be served for any unrecognized path (to allow refreshing on a frontend route). This ensures smooth navigation without 404s.

State Synchronization: The server must keep its in-memory state in sync with the filesystem. It can load the feature registry, progress log, and config on startup
GitHub
GitHub
, and then watch for changes. Each API write will update the files on disk (using existing internal utilities – note that the CLI already has functions for load/save of features and progress, which we can reuse
GitHub
GitHub
). If an external change is detected (e.g. user runs a CLI command in parallel that changes a file), we should pick up that change. Possible implementation: use file timestamps or a filesystem watcher to trigger reloads of data, or have the UI ping an endpoint that simply returns a flag if data changed (the WebSocket approach is more elegant: the server can send a “data changed” event). The MCP server built into Klondike already exposes similar operations and could be repurposed – for instance, it has tools to get_features, start_feature, etc.
GitHub
. We can leverage that logic for our HTTP API to ensure consistency with how CLI does things (the MCP functions already load and save the JSON files safely on each operation). In essence, Klondike Serve’s backend is a thin HTTP wrapper around Klondike’s core operations and data models.

Security (Local Context): Since the server has no auth and runs locally, we assume a trusted environment. We will bind to localhost by default to prevent remote access. We won’t implement user accounts or roles. We also will avoid executing arbitrary commands – all operations are constrained to the predefined feature/session management. One security consideration: if we allow file uploads for evidence, we must ensure the file stays in the project (maybe copy it to a .klondike/evidence/ folder) or handle paths carefully. But likely we just take a path string as evidence (user would manually point to a file already in project). This is an edge detail; overall, security risk is low given local usage and no external exposure.

Performance & Resource Use: The server should be lightweight – it will typically handle a single user’s requests. Memory footprint will mostly be the loaded JSON data and the React app assets. The chosen framework (FastAPI or Flask) should handle serving ~hundreds of requests per second easily on a dev machine, which is plenty (UI will generate minimal load). Ensure the server shuts down cleanly when klondike serve is terminated (e.g. Ctrl+C in the terminal should stop the web server thread). We might consider printing a message like “Press Ctrl+C to quit” after launching, for clarity.

UI Design Notes

Technology & Framework: We will build the front-end as a single-page application (SPA) using React for its robust ecosystem and component model, coupled with Tailwind CSS for rapid, consistent styling. This combination is a proven approach for interactive, real-time dashboards, offering fast development and a clean, maintainable UI codebase
dev.to
. React’s component-based architecture and state management make it ideal for dynamically updating views as data changes, while Tailwind’s utility-first CSS will ensure we can create a modern, responsive design without writing a lot of custom CSS
dev.to
. The UI will likely be organized as a few high-level React components corresponding to the main views (Dashboard, SpecExplorer/FeatureList, FeatureDetails, ActivityLog, ConfigEditor) and use routing (e.g. React Router) to navigate between them. Real-time updates will be handled via React hooks and the WebSocket – for example, using a useEffect hook to open a WebSocket connection to the server and listening for messages that indicate updates, then updating the relevant state
dev.to
. This will allow the UI to seamlessly reflect live data changes without manual intervention. We will also utilize libraries as needed for charts or code highlights – e.g. use a small chart library for the progress pie, or a timeline component for sessions, etc. The end goal is a polished web app experience running off the local server.

Look & Feel: The design will be clean, intuitive, and aligned with modern web app aesthetics. Using Tailwind, we’ll adopt a neutral/light color scheme by default (with soft grays for backgrounds, a primary accent color for highlights, etc.), ensuring that important information (like statuses) is color-coded and accompanied by icons or symbols familiar from the CLI (for consistency, e.g. use ⏳, 🔄, ✅, 🚫 alongside text for statuses). The layout likely includes a top navigation bar or sidebar for switching between main sections:

A sidebar menu could list: Dashboard, Spec Explorer, Activity Log, Config Editor (and perhaps a toggle for dark mode, if we choose to support that easily via Tailwind’s dark: classes). This sidebar would make it easy to jump between views. The current section should be highlighted. The sidebar can also display the project name at the top for context.

The Dashboard page will use a card-based layout or grid to show different info panels. For example, a card showing “Overall Progress: 60% (30/50 features completed)” with a progress bar or donut chart; a card for “Project Status: In Progress (Session 5 active)” or “All features verified” etc.; a panel listing maybe the top 3 priority features (with short descriptions) as actionable items; and a panel for recent commits (list the last few commit messages with time). Key metrics should use larger text or charts to stand out. This page is the quick summary for the user each time they visit the UI.

The Spec Explorer likely will be a two-column layout: on the left, a scrollable list or table of features; on the right, the detail view of the selected feature (Task Viewer). Alternatively, the feature detail might be a separate route/page (e.g. clicking a feature navigates to /feature/F001 view). But a master-detail split view can improve productivity (you can click through features quickly). In the list, each feature entry could be a collapsible row or just a line with key info. We might include quick-action buttons in the list (e.g. a “Start” ▶️ icon next to features not started, which directly marks it in-progress without fully opening detail). But these are enhancements; at minimum, clicking goes to detail. The detail view will organize feature information with clear subheadings: Description, Acceptance Criteria (perhaps a checklist UI so user can tick them off conceptually – though ticking might not directly do anything unless we tie it to verification progress), Dependencies (if any), Notes/Implementation Notes, and Evidence (if verified). If the feature is not verified, an “Evidence” section can be empty or hidden. Edit controls (pencils or edit buttons) should be next to editable fields or an overall “Edit” mode toggle that turns fields into form inputs. Use modals for multi-field edits if needed (e.g. a modal form to add a new acceptance criterion).

For statuses, use styling: e.g. Verified in green with a check icon, In Progress in blue, Blocked in red with a stop icon, Not Started in gray. Possibly represent status as a badge or pill UI element. This will visually align with how the CLI prints statuses in color
GitHub
.

The Activity Log page can be a vertical timeline or simply a list of session cards. A timeline could show each session as an expandable item on a timeline with date markers. Each session entry should present the summary (focus) as a title, and inside show the lists of Completed, In Progress, Blockers, Next Steps. We can style these lists with icons (e.g. a checkmark list for completed items, an hourglass or spinner for in-progress items, warning icon for blockers, lightbulb or arrow for next steps). If using a card style, each session card would contain the same info in sections. The session cards could also indicate the agent name and duration. If a session is currently ongoing, highlight it (maybe a different border or a “ongoing” label). After listing sessions, we might also show commit history items (with commit hash short and message) in the timeline, possibly interwoven by timestamp if we want a true chronological timeline of all project events. This could be visually appealing and informative, though an MVP might keep commits separate.

The Config Editor will be a simple form. Likely we’ll present each config entry with a label and an input. We might group related settings (for example: Defaults: category & priority, Progress Log: auto-regenerate and output path, Verification: verified_by, Project Info: PRD link, Klondike version, Agents: configured_agents list). The UI should display help text (from the comments we have in config save logic
GitHub
GitHub
) so the user knows what each setting does. A “Save” button will apply changes. We should provide feedback like “Settings saved successfully” or highlight fields that have invalid data (though most are simple types).

Responsive Design: The interface should be responsive to different screen sizes. On smaller screens (like a laptop or tablet), the sidebar might collapse into a hamburger menu and views might stack vertically. For example, on a narrow screen, the Spec Explorer could switch to a single-column mode where the feature list turns into a dropdown or accordion, and the detail view is below or on a separate screen. Tailwind’s responsive utility classes will help ensure the design adapts (e.g. using grid-cols-2 on large screens vs. grid-cols-1 on small, etc.). While most usage will likely be on a desktop browser, making the UI at least somewhat usable on a tablet could be beneficial (mobile phone support is lower priority, but the basics should still be accessible).

Visual Identity: Although this is an internal tool, giving it a bit of personality can improve user experience. We might incorporate the “🎴 Klondike” playing-card theme subtly – e.g. use a card icon or suit symbol in the UI header, or style the dashboard cards with a motif reminiscent of playing cards for fun. However, the primary focus is clarity and professionalism, so any thematic decoration should be minimal. We will maintain consistency with Klondike’s existing branding (the README uses a playing card emoji and gold color perhaps).

Feedback and Confirmation: Use modals and toast notifications to confirm user actions. For example, after adding a feature, show a toast “Feature F051 added.” If the user attempts to navigate away with unsaved edits, show a confirmation “Discard changes?” prompt. When connecting to the server, if the connection drops (server stopped), the UI should alert the user “Connection lost – please ensure klondike serve is running.” These polish items ensure the user is never confused about what’s happening.

Icons and Libraries: Leverage an icon library (such as HeroIcons or FontAwesome) for consistency with Tailwind (HeroIcons works nicely with Tailwind). Icons for edit (pencil), delete (trash, though deleting a feature might not be allowed by design, which is something to clarify), save (check), etc., should be used with accessible tooltips. If using color, ensure sufficient contrast and consider colorblind-friendly choices (e.g. also use different shapes or text labels, not color alone, to indicate status).

Testing & Quality: As part of development, we will test the UI with sample projects to ensure all data renders correctly. We should test a scenario with many features, a scenario with none, with long descriptions, blocked features, etc., to make sure the layout holds up. Also verify that all CLI operations triggered via UI indeed reflect in the .klondike files (and vice versa).

API Outline

(Below is an outline of the API endpoints and their purposes, aligning with the functional needs. All endpoints are assumed to be prefixed by /api and return JSON responses.)

GET /api/status – Project Status Overview. Returns a JSON object summarizing the project’s state:

project: project name

version: project/version (if tracked)

progress: { total features, passing features, percent (completion) }
GitHub

by_status: counts of features by status (keys: “not-started”, “in-progress”, “blocked”, “verified”)
GitHub

current_session: details of the current session if one is active (session number, focus, etc., or null if none)
GitHub

priority_features: list of up to 3 high-priority features (each with id, description, priority) that are next to do
GitHub
.

It may also include a short recent commit list or git status summary (e.g. embed a git_status string and an array recent_commits). (Alternatively, commits could be fetched via a separate endpoint, see below.)
Use: Populating Dashboard (progress bar, counts, current session info, etc.).

GET /api/features – List All Features. Returns a JSON array of feature objects, or an object with both project info and features. Each feature object includes key fields of the feature registry:

id, description, category, priority, status, passes (bool if tests/evidence passed), etc.
GitHub
GitHub
.

It might omit very detailed fields like acceptance criteria or notes for brevity. There is an optional query parameter status to filter by status
GitHub
 (e.g. /api/features?status=blocked returns only blocked features).
Use: Spec Explorer list, possibly with client-side filtering as well.

POST /api/features – Create New Feature. Request body JSON with new feature data:

required: description (string),

optional: category (string), priority (int), criteria (list of strings for acceptance criteria), notes (string).

The server will assign a new id (next sequential like F00X) and default any missing fields (e.g. if no category given, use config default_category
GitHub
).

It adds the feature to the registry and returns the full feature object or an error if something is wrong (e.g. description empty).
Use: Adding features via UI form.

GET /api/features/{id} – Get Feature Details. Returns a detailed feature object for feature with ID {id}. This includes all fields from the registry for that feature: description, category, priority, status, passes, acceptanceCriteria (full list), dependencies, blocked_by (if any), verified_by, verified_at, evidence_links (if any), last_worked_on, notes, etc.
GitHub
GitHub
. If the feature is not found, returns 404 with error.
Use: Loading data for the Task Viewer (feature detail page) on demand (if we don’t already have it from the list).

PUT /api/features/{id} – Update Feature. Allows editing a feature’s data. The request body can include any of the editable fields: description (if allowed), category, priority, acceptanceCriteria (possibly the full list or indications of additions), notes. The server will update those fields for the specified feature and save the changes. Certain fields that should not change (like id obviously, or perhaps we consider description immutable in some workflows) will be ignored or cause an error if included (to be defined). The response returns the updated feature object, or an error if the feature doesn’t exist or validation fails.
Use: Saving edits made in the UI (e.g. updating notes or criteria).

POST /api/features/{id}/start – Start Feature Work. Marks feature {id} as in-progress (status change). The server will load the registry, find the feature, set its status to in-progress and update last_worked_on timestamp
GitHub
. It will also update the progress log’s quick reference (priority features) to reflect this new active feature if needed
GitHub
. If another feature was already in progress, the server may include a warnings field in the response (listing IDs of other in-progress features)
GitHub
GitHub
, so the UI can alert the user that multiple features are now marked in progress. Response: success message and the feature’s new status
GitHub
, or error if feature not found.
Use: User clicking “Mark as In Progress” on a feature.

POST /api/features/{id}/block – Block Feature. Marks feature {id} as blocked. Expects a JSON body with a reason field (string explaining why blocked). The server will set the feature’s status to blocked and record the reason in blocked_by
GitHub
. It also updates last_worked_on. Returns success with the updated feature status and the reason recorded
GitHub
, or an error if feature not found. If reason is missing, it returns an error “Reason is required”
GitHub
GitHub
 (the UI should ensure to provide it).
Use: User blocking a feature and explaining the blocker.

POST /api/features/{id}/verify – Verify Feature. Marks feature {id} as completed/verified. Expects evidence in the request body (a string or list of strings, e.g. file paths, describing proof of completion). The server checks that evidence is provided (if not, responds with error “Evidence is required”)
GitHub
. If okay, it updates the feature: status = verified, passes = true, sets verified_at timestamp to now, verified_by (could use a default like config.verified_by which is typically "coding-agent" or could be set to something like "user")
GitHub
GitHub
, and saves the provided evidence links in the feature’s evidence_links field
GitHub
GitHub
. It will also update overall registry metadata counts (increment passing_features etc.)
GitHub
. Then returns success with the updated feature info (including status now “verified” and evidence list)
GitHub
. Errors if not found, or if evidence missing.
Use: User marking a feature as completed with proof (triggered by “Verify” in UI).

GET /api/progress – Get Progress Log. Returns the entire project progress log (session history). The JSON would contain:

projectName, startedAt (project start date), currentStatus (e.g. “Session Ended” or “In Progress”),

sessions: an array of session entries. Each session entry includes sessionNumber, date, agent, duration, focus (summary), completed (list of items), inProgress (list), blockers (list), nextSteps (list), technicalNotes (list)
GitHub
GitHub
. These correspond exactly to what is in agent-progress.json for each session.

Optionally, a trimmed down quick reference (like a list of current priority features) might be included, but that is already in status; the main use is the session log.
Use: Populating the Activity Log view with all sessions.

POST /api/session/start – Start a Session. Begins a new coding session. The request could include a focus string (describing what the session will work on; if empty, a default like “General development” is used)
GitHub
. The server will perform the same steps as klondike session start: it may check Git status and artifact consistency first (and possibly return any warnings about uncommitted changes or metadata mismatches as part of response)
GitHub
GitHub
. Then it creates a new session entry with the next session number, today’s date, agent set to “Coding Agent” (or perhaps we label it “User” if launched manually), duration “(in progress)”, focus as provided, and an initial in_progress list containing “Session started”
GitHub
GitHub
. It sets current_status in progress log to “In Progress”. This is saved to file and the markdown is regenerated. Response includes something like { success: true, sessionNumber: N } or the full session data. After this, the project’s status (accessible via GET /api/status) will reflect a session is active.
Use: Possibly triggered by a “Start Session” button in UI, though this is optional.

POST /api/session/end – End the Session. Ends the currently active session. Request body can have:

summary (string to overwrite the session’s focus/summary),

completed (comma-separated or list of completed items descriptions),

blockers (list of blockers encountered, if any),

nextSteps (list of recommended next steps).
The server finds the latest session (if none active, returns error). It then updates that session entry: sets duration to a calculated value or a placeholder (CLI uses "~session")
GitHub
GitHub
, clears the in_progress list (since session is ending)
GitHub
GitHub
, and fills in the provided completed, blockers, nextSteps. If nextSteps wasn’t provided, CLI auto-generates some based on priority features
GitHub
 – our server can do the same (e.g. populate “Continue <FeatureX>” for top 3 not done). It then sets progress log’s current_status to "Session Ended"
GitHub
 and saves everything. If auto_commit option was given (we might allow a boolean flag), then the server will perform a git commit with a standardized message
GitHub
 (assuming the repo is initialized and git operations are available – this is advanced and can be skipped initially or always false unless we implement it fully). Response returns success and maybe the updated session info.
Use: Triggered by “End Session” in UI, capturing the user’s summary of the session.

GET /api/config – Get Config Settings. Returns the current configuration (the content of .klondike/config.yaml) as JSON. For example:

{
  "default_category": "core",
  "default_priority": 2,
  "verified_by": "coding-agent",
  "progress_output_path": "agent-progress.md",
  "auto_regenerate_progress": true,
  "prd_source": "<URL or null>",
  "klondike_version": "0.2.16",
  "configured_agents": ["copilot", "claude"]
}


(The last two fields are mostly informational)
GitHub
GitHub
. This allows the UI to populate the Config Editor fields with current values.

PUT /api/config – Update Config. Accepts a JSON object with one or more config fields to change (same keys as above). The server updates the Config in memory and writes out a new config.yaml (retaining comments where possible, though it may rewrite fully in a standard format). It returns the updated config or success status. If an unknown field is provided or a value is invalid (e.g. negative priority), it returns an error. Some changes might trigger side effects; for example, if default_category changes, it doesn’t retroactively change existing features but will be used for new ones. Most changes are straightforward. The UI should probably reload the config (GET /api/config) after save to ensure it’s showing the persisted values.

GET /api/commits – Recent Commits. (Optional endpoint) Returns a list of recent git commits for the project’s repository. This could include commit hash, author, date, and message. The CLI internally has get_recent_commits(5) which is used for status
GitHub
, so we could expose that. E.g., response: [ { "hash": "abc123", "date": "2025-12-10", "message": "Fix bug in feature X" }, {... up to 5} ]. If the project is not a git repo, it might return an empty list or an error flag. This helps populate the Activity Log or Dashboard commit list beyond just what’s in the status summary.

All these endpoints are unsecured (local use). The server will log requests and errors to console for debugging. The API design is meant to mirror the CLI’s capabilities one-to-one
GitHub
, ensuring that anything you could do via Klondike CLI, you can do via an HTTP request from the UI. This symmetry also means we can reuse the existing internal functions (as demonstrated by the MCP server support which already defines similar tools for features and sessions
GitHub
).

The WebSocket endpoint (if using) might be something like GET /api/updates (upgrade to WS). When connected, the server can send messages like {"event":"feature_updated","feature": <feature_id or data>} or {"event":"session_started","session": N}, etc. We will define a small set of event types: e.g. featureAdded/Updated/Removed, sessionStarted/Ended, configChanged, etc., or even a generic “dataChanged” event that tells the client to refetch certain data. The exact schema can be defined in implementation; the key is the UI can subscribe and react accordingly.

Non-Goals

Multi-User Access / Authentication: This UI is not intended to be a multi-user or remotely hosted tool. We will not implement user accounts, login screens, or role-based access control. The server will not include authentication mechanisms – it’s assumed to be run locally by the project owner. Collaborative multi-user scenarios (multiple people looking at the same dashboard remotely) are out of scope. (In the future, if needed, one could run klondike serve on a server and expose it, but officially we are not focusing on that use case now.)

Cloud or Remote Deployment: The feature is designed for local development environments. We do not plan any deployment to cloud or handling of public URLs/domain, containerization, etc., as part of this PRD. There will be no built-in support for deploying this UI as a persistent web service for a team. Users should run it on their machine for their project. Any networking beyond localhost (like accessing the UI from a phone via LAN) is incidental and not explicitly supported (though if one opens the firewall, it might work – but we won’t invest in that scenario).

AI Agent Integration via UI: While Klondike is about AI coding agent workflows, this initial UI will not attempt to embed or replace the AI interaction interface. That means we are not building a chat interface for Copilot/Claude in the UI, nor starting/stopping the AI agent from the browser. The focus is on project management data. (The CLI’s agent sessions will still be run through the terminal or VSCode as they are today.) We also are not exposing the MCP server functionality via the UI except as it overlaps with project data management. For example, we won’t surface the low-level MCP tool operations or allow arbitrary execution of CLI commands through the UI, aside from the specific ones in scope (feature and session management).

Advanced Workflow Automation: Features like automatically triggering test runs on verify, or refreshing the UI continuously with git polling beyond what’s described, are not in scope. We won’t implement things like real-time code diff views of changes, CI integration, or other complex devops features. The UI’s purpose is to reflect and manipulate the state in Klondike’s files; it’s not a full project management or CI dashboard (e.g., no Kanban board, no test runner output panel). Users will still rely on their IDE/terminal for coding and running tests; the UI is an adjunct for tracking specs and progress.

Deleting or Reordering Core Artifacts: We do not plan to support deleting features or reordering the progress log via the UI in this iteration. The CLI doesn’t provide a direct feature delete command, and to keep things simple and safe, the UI will not expose destructive actions like removing a feature from the registry (one can mark as “removed” or just ignore if not needed). Similarly, editing past session logs (beyond adding an end summary before ending) is not supported – the log is an archive.

Complex Customization: The PRD does not include building a theming system, plugin system, or extensive customization options for the UI. For example, we won’t implement custom dashboard widgets or user-defined views in V1. The UI will be as straightforward as possible to meet the immediate needs, using the chosen tech stack’s defaults (e.g. styling via Tailwind classes rather than requiring users to provide custom CSS).

Open Questions

During development of Klondike Serve, we expect to address the following open questions:

Port and Launch Behavior: What port should the server run on by default, and should it automatically open the web browser? A likely default is port 8000, but we should confirm no conflicts. Auto-opening the browser can improve UX but might be unexpected for some; perhaps make it optional (e.g. klondike serve --open). Alternatively, simply print a clear message with the URL. We need to decide the best developer experience here.

WebSocket vs Polling Implementation: While we prefer WebSockets for real-time updates, this adds complexity (especially for users opening the page after some changes already occurred – handling initial sync vs incremental events). We need to evaluate if a simpler periodic poll might suffice initially, and whether the added value of push updates is worth the complexity in V1. Given performance should be fine, leaning towards WebSocket is okay
dev.to
, but we should plan fallback behavior if WebSocket fails.

Handling External Edits: If the user runs CLI commands or if an AI agent session updates the project concurrently with the UI open, how do we handle potential conflicts? For instance, if a feature is marked verified via CLI while the UI is showing it as not-started, the UI should update (via real-time events or at least on focus). We might implement file watchers on the server (using watchdog library or similar) to detect changes in features.json or agent-progress.json made outside the API. Alternatively, we rely on the fact that most changes will come through either CLI or UI but not simultaneously. We should clarify the priority: probably the last writer wins, and the UI always eventually reflects the actual file content. It’s an edge case for single-user, but important for robustness.

Evidence Handling: How should the UI allow users to provide evidence when verifying a feature? Currently, CLI expects a file path or comma-separated paths to proofs (like screenshots or test output files)
GitHub
. In a UI, ideally we’d let the user either input a path or even upload a file. If uploading, where do we store it? Possibly in a .klondike/evidence/ folder and then provide that path to the feature. Upload support would be nice, but it complicates things (need to handle file saving). We may choose a simpler route: have the user run tests externally and just type a short note or path (e.g. “tests/pass_report.txt”) as evidence. This might be clarified via user feedback – initial version could just support text input for evidence path/URL.

CLI Parity and Future Commands: Are there other CLI subcommands we should incorporate into the UI now or later? For example, klondike report (generating a report) – perhaps in the UI a user might want to download a progress report or PRD. Or klondike import/export-features – not likely needed in UI, as that’s a one-time CLI action. We should confirm that all key daily-use functionalities are covered. The core ones we identified (status, feature add/list/edit/start/verify/block/show, session start/end, config) seem to cover the primary workflow. New CLI commands (like if future versions add more agents or something) could also lead to UI changes, but we will cross that when it happens. The PRD should remain focused on the current spec.

Testing & Debugging Mode: Should we include any debugging interfaces (like viewing the raw JSON or logs) in the UI? Possibly an "Advanced" section could allow the user to see raw JSON content of features or progress (for troubleshooting), but that might not be necessary for most. Instead, we might rely on the fact that those files are accessible in the project if needed. We’ll likely skip an advanced JSON view to keep UI clean, unless during development we find it useful.

Framework for Backend: We assume FastAPI, but if for some reason we use Flask, will it handle WebSockets easily? (Flask would require an extension or using Socket.IO, which is more overhead). FastAPI’s uvicorn server can handle async and WS well. We’ll need to package this appropriately. Ensuring the server can run on Windows, Mac, Linux consistently (no OS-specific issues) is also something to verify.

Performance with Larger Projects: If a project had hundreds of features or a very large progress log, would our UI still be smooth? We might pre-emptively consider adding pagination or lazy-loading for extremely large lists (though unlikely in initial target use). This is a potential future concern, but we note it to ensure our design can handle growth (maybe 100+ features, 50+ sessions) without major tweaks.

Error Handling and Recovery: What happens if the server crashes or is stopped while the UI is open? We should handle that on the UI side (detect disconnection and prompt user). Also, if the user tries to start the server when another process is using the port, how do we communicate that? Possibly the CLI could detect and offer an alternate port. We should decide whether to implement a simple port check or let it error out gracefully (“Address in use” message). Similarly, if .klondike is missing, klondike serve should error with a clear message (maybe, “No Klondike project found in this directory. Run klondike init first.”).

Future Enhancements: While out of scope now, we leave questions for future: Might we integrate a mini markdown viewer for the PRD itself if a PRD link is provided? (E.g. show the contents of the PRD markdown in the UI for reference.) Or perhaps allow one-click opening of the PRD source. This could strengthen the UI as a one-stop project overview tool. Also, could we allow triggering an AI agent session from the UI (like a “Run Copilot on this feature” button)? That would be complex (would need to launch copilot CLI and stream output), so likely for future brainstorming. For now, we focus on core management features.

By addressing these questions during design & development, we will refine the Klondike Serve experience to be robust and user-friendly. The result will empower users to oversee their AI-driven coding projects with clarity and convenience, complementing the powerful Klondike CLI workflow with an equally powerful GUI.