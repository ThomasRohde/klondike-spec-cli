"""Web UI server command for Klondike Spec CLI.

Provides a FastAPI-based web interface for managing features, sessions, and project progress.
Includes WebSocket support for real-time updates and file watching for external CLI changes.
"""

import logging
import signal
import sys
import threading
import webbrowser
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path
from types import FrameType
from typing import Any

from pith import PithException, echo

from .._version import __version__
from ..data import get_klondike_dir


def serve_command(
    port: int = 8000,
    host: str = "127.0.0.1",
    open_browser: bool = False,
) -> None:
    """Start FastAPI web server for Klondike Spec project management.

    Launches a web UI for managing features, sessions, and project progress.
    Requires .klondike directory in current directory.

    Args:
        port: Port to run server on (default: 8000)
        host: Host to bind server to (default: "127.0.0.1")
        open_browser: Open browser automatically (default: False)

    Examples:
        >>> serve_command()  # Start on http://127.0.0.1:8000
        >>> serve_command(port=3000)  # Use custom port
        >>> serve_command(host="0.0.0.0")  # Allow external connections
        >>> serve_command(open_browser=True)  # Auto-launch browser

    Raises:
        PithException: If FastAPI/uvicorn not installed, no .klondike directory,
                      or port already in use.
    """
    try:
        import uvicorn
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect
        from fastapi.responses import FileResponse, HTMLResponse
        from fastapi.staticfiles import StaticFiles
    except ImportError as err:
        raise PithException(
            f"FastAPI/uvicorn import failed: {err}\n"
            "Try reinstalling: pip install --force-reinstall klondike-spec-cli"
        ) from err

    try:
        from watchdog.events import FileSystemEvent, FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError as err:
        raise PithException(
            f"watchdog import failed: {err}\n"
            "Try reinstalling: pip install --force-reinstall klondike-spec-cli"
        ) from err

    # Verify .klondike directory exists
    root = Path.cwd()
    klondike_dir = get_klondike_dir(root)
    if not klondike_dir:
        raise PithException(
            "No .klondike directory found in current directory.\n"
            "Run 'klondike init' first to initialize a project."
        )

    # Initialize FastAPI app
    app_instance = FastAPI(
        title="Klondike Spec CLI",
        description="Project management web UI for agent workflows",
        version=__version__,
    )

    # Custom middleware to add CORS headers for local development
    from starlette.requests import Request
    from starlette.responses import Response

    @app_instance.middleware("http")
    async def add_cors_headers(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Add CORS headers to all responses for local development."""
        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            from starlette.responses import Response

            response = Response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response

        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

    # WebSocket connection manager
    class ConnectionManager:
        """Manages WebSocket connections and broadcasts events."""

        def __init__(self) -> None:
            self.active_connections: list[WebSocket] = []

        async def connect(self, websocket: WebSocket) -> None:
            await websocket.accept()
            self.active_connections.append(websocket)

        def disconnect(self, websocket: WebSocket) -> None:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

        async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
            """Broadcast an event to all connected clients."""
            message = {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)

            # Clean up disconnected clients
            for conn in disconnected:
                self.disconnect(conn)

    manager = ConnectionManager()

    # Store reference to the main event loop for cross-thread broadcasting
    main_loop: Any = None

    # File watcher for detecting external CLI changes
    class KlondikeFileHandler(FileSystemEventHandler):
        """Watches .klondike directory for changes."""

        def __init__(self, manager: ConnectionManager, root_path: Path) -> None:
            self.manager = manager
            self.root_path = root_path
            self.last_event_time: dict[str, float] = {}
            super().__init__()

        def _should_process_event(self, path: str) -> bool:
            """Debounce events - only process if > 100ms since last event for this file."""
            import time

            now = time.time()
            if path in self.last_event_time:
                if now - self.last_event_time[path] < 0.1:
                    return False
            self.last_event_time[path] = now
            return True

        def on_modified(self, event: FileSystemEvent) -> None:
            if event.is_directory:
                return

            path = Path(str(event.src_path))
            if not self._should_process_event(str(path)):
                return

            # Detect which file changed and emit appropriate event
            if path.name == "features.json":
                self._emit_features_changed()
            elif path.name == "agent-progress.json":
                self._emit_session_changed()
            elif path.name == "config.yaml":
                self._emit_config_changed()

        def _schedule_broadcast(self, event_type: str, data: dict[str, Any]) -> None:
            """Schedule a broadcast to run on the main asyncio event loop."""
            import asyncio

            nonlocal main_loop
            if main_loop is None:
                return

            try:
                # Use run_coroutine_threadsafe to schedule from watchdog thread
                asyncio.run_coroutine_threadsafe(
                    self.manager.broadcast(event_type, data),
                    main_loop,
                )
            except Exception:
                pass  # Silently ignore errors in file watcher

        def _emit_features_changed(self) -> None:
            """Emit featureUpdated event."""
            try:
                from ..data import load_features

                registry = load_features(self.root_path)
                self._schedule_broadcast(
                    "featureUpdated",
                    {
                        "total": len(registry.features),
                        "passing": sum(1 for f in registry.features if f.passes),
                    },
                )
            except Exception:
                pass  # Silently ignore errors in file watcher

        def _emit_session_changed(self) -> None:
            """Emit sessionUpdated event."""
            try:
                from ..data import load_progress

                progress = load_progress(self.root_path)
                self._schedule_broadcast(
                    "sessionUpdated",
                    {
                        "status": progress.current_status,
                        "sessionCount": len(progress.sessions),
                    },
                )
            except Exception:
                pass

        def _emit_config_changed(self) -> None:
            """Emit configChanged event."""
            self._schedule_broadcast("configChanged", {})

    # Start file watcher
    event_handler = KlondikeFileHandler(manager, root)
    observer = Observer()
    observer.schedule(event_handler, str(klondike_dir), recursive=False)
    observer.start()

    # Get static files directory from package
    static_dir = Path(__file__).parent.parent / "static"
    if not static_dir.exists():
        raise PithException(
            f"Static files directory not found: {static_dir}\n"
            "This may indicate a broken installation."
        )

    # Mount static files
    app_instance.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    @app_instance.on_event("startup")
    async def on_startup() -> None:
        """Capture the main event loop for cross-thread broadcasting."""
        import asyncio

        nonlocal main_loop
        main_loop = asyncio.get_running_loop()

    @app_instance.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok", "version": __version__}

    @app_instance.websocket("/api/updates")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time updates.

        Emits events:
        - featureAdded: When a new feature is added
        - featureUpdated: When features change (add/update/status)
        - sessionStarted: When a session starts
        - sessionEnded: When a session ends
        - sessionUpdated: When session data changes
        - configChanged: When configuration is updated
        """
        await manager.connect(websocket)
        try:
            # Send initial sync event
            from ..data import load_features, load_progress

            registry = load_features(root)
            progress = load_progress(root)

            await websocket.send_json(
                {
                    "type": "connected",
                    "data": {
                        "features": {
                            "total": len(registry.features),
                            "passing": sum(1 for f in registry.features if f.passes),
                        },
                        "session": {
                            "status": progress.current_status,
                            "sessionCount": len(progress.sessions),
                        },
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Keep connection alive and wait for disconnect
            while True:
                # Wait for messages (though we don't expect any from client)
                try:
                    await websocket.receive_text()
                except WebSocketDisconnect:
                    break
        except WebSocketDisconnect:
            pass
        finally:
            manager.disconnect(websocket)

    @app_instance.websocket("/ws/presence")
    async def presence_websocket(websocket: WebSocket) -> None:
        """WebSocket endpoint for presence/collaborative features.

        Used by PresenceIndicator component to show active users.
        Currently accepts connections but doesn't implement full presence logic.
        """
        await manager.connect(websocket)
        try:
            # Send connected confirmation
            await websocket.send_json(
                {
                    "type": "presence",
                    "data": {"status": "connected"},
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Keep connection alive
            while True:
                try:
                    data = await websocket.receive_text()
                    # Echo back for now (implement presence logic later)
                    await websocket.send_json(
                        {
                            "type": "presence_ack",
                            "data": {"received": data},
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                except WebSocketDisconnect:
                    break
        except WebSocketDisconnect:
            pass
        finally:
            manager.disconnect(websocket)

    @app_instance.get("/api/status")
    async def api_status() -> dict[str, Any]:
        """Get project status overview.

        Returns project metadata, progress counts, feature status summary,
        current session info, priority features, and recent git commits.
        """
        from ..data import load_config, load_features, load_progress
        from ..git import get_git_status, get_recent_commits

        try:
            # Load project data
            load_config(root)
            registry = load_features(root)
            progress_log = load_progress(root)

            # Calculate progress
            total = len(registry.features)
            passing = sum(1 for f in registry.features if f.passes)
            percent = round((passing / total * 100), 1) if total > 0 else 0.0

            # Count features by status
            by_status = {
                "not-started": 0,
                "in-progress": 0,
                "blocked": 0,
                "verified": 0,
            }
            for feature in registry.features:
                status_key = (
                    feature.status.value if hasattr(feature.status, "value") else feature.status
                )
                if status_key in by_status:
                    by_status[status_key] += 1

            # Get current session (if active)
            current_session = None
            if progress_log.sessions and progress_log.current_status == "In Progress":
                last_session = progress_log.sessions[-1]
                current_session = {
                    "id": last_session.session_number,
                    "focus": last_session.focus,
                    "agent": last_session.agent,
                    "date": last_session.date,
                }

            # Get priority features
            priority_features = []
            for pf in progress_log.quick_reference.priority_features[:3]:
                priority_features.append(
                    {
                        "id": pf.id,
                        "description": pf.description,
                        "status": pf.status,
                    }
                )

            # Get git status and recent commits
            git_status_obj = get_git_status(root)
            git_data = None
            if git_status_obj.is_git_repo:
                recent_commits = get_recent_commits(5, root)
                git_data = {
                    "branch": git_status_obj.current_branch,
                    "clean": git_status_obj.clean,
                    "is_clean": git_status_obj.clean,  # Alias for frontend
                    "staged": git_status_obj.staged_count,
                    "unstaged": git_status_obj.unstaged_count,
                    "untracked": git_status_obj.untracked_count,
                    "recent_commits": [
                        {
                            "hash": c.short_hash,
                            "message": c.message,
                            "author": c.author,
                            "date": c.date,
                        }
                        for c in recent_commits
                    ],
                }

            # Check if a session is currently active
            is_session_active = (
                progress_log.current_status == "In Progress" and current_session is not None
            )

            return {
                "project_name": root.name,
                "project_version": registry.version,
                "completion_percentage": percent,
                "feature_counts": {
                    "total": total,
                    "verified": by_status["verified"],
                    "blocked": by_status["blocked"],
                    "in_progress": by_status["in-progress"],
                    "not_started": by_status["not-started"],
                },
                "is_session_active": is_session_active,
                "current_session": current_session,
                "last_session": current_session,  # Keep for backwards compat
                "priority_features": priority_features,
                "git_status": git_data,
            }

        except Exception as e:
            return {"error": str(e)}

    @app_instance.get("/api/features")
    async def api_features_list(status: str | None = None) -> dict[str, Any]:
        """Get all features with optional status filter.

        Query Parameters:
            status: Filter by status (not-started, in-progress, blocked, verified)

        Returns:
            List of features with all properties.
        """
        from ..data import load_features
        from ..models import FeatureStatus

        try:
            registry = load_features(root)
            features = registry.features

            # Apply status filter if provided
            if status:
                try:
                    status_filter = FeatureStatus(status)
                    features = [f for f in features if f.status == status_filter]
                except ValueError:
                    return {
                        "error": f"Invalid status: {status}. Use: not-started, in-progress, blocked, verified"
                    }

            return {
                "features": [f.to_dict() for f in features],
                "total": len(features),
            }
        except Exception as e:
            return {"error": str(e)}

    @app_instance.get("/api/features/{feature_id}")
    async def api_feature_get(feature_id: str) -> dict[str, Any]:
        """Get single feature by ID.

        Path Parameters:
            feature_id: Feature ID (e.g., F001)

        Returns:
            Feature details or 404 error.
        """
        from ..data import load_features

        try:
            registry = load_features(root)
            registry._build_index()

            if feature_id not in registry._feature_index:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail=f"Feature not found: {feature_id}")

            feature = registry._feature_index[feature_id]
            return feature.to_dict()
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.post("/api/features")
    async def api_feature_create(feature_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new feature.

        Request Body:
            {
                "description": str (required),
                "category": str (optional, default: "core"),
                "priority": int (optional, default: 2),
                "acceptance_criteria": list[str] (optional),
                "notes": str (optional),
                "dependencies": list[str] (optional)
            }

        Returns:
            Created feature with auto-assigned ID.
        """
        from datetime import datetime

        from ..data import load_features, save_features
        from ..models import Feature, FeatureStatus

        try:
            # Validate required fields
            if not feature_data.get("description"):
                from fastapi import HTTPException

                raise HTTPException(status_code=400, detail="Description is required")

            registry = load_features(root)

            # Auto-assign next feature ID
            existing_ids = [
                int(f.id[1:])
                for f in registry.features
                if f.id.startswith("F") and f.id[1:].isdigit()
            ]
            next_id = max(existing_ids) + 1 if existing_ids else 1
            feature_id = f"F{next_id:03d}"

            # Validate priority range (1-5)
            priority = feature_data.get("priority", 2)
            if not isinstance(priority, int) or priority < 1 or priority > 5:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=400,
                    detail="Priority must be an integer between 1 and 5",
                )

            # Create new feature
            new_feature = Feature(
                id=feature_id,
                description=feature_data["description"],
                category=feature_data.get("category", "core"),
                priority=priority,
                acceptance_criteria=feature_data.get("acceptance_criteria", []),
                notes=feature_data.get("notes"),
                dependencies=feature_data.get("dependencies", []),
                status=FeatureStatus.NOT_STARTED,
                passes=False,
            )

            # Add to registry and save
            registry.features.append(new_feature)
            registry._invalidate_index()

            # Update metadata
            registry.metadata.total_features = len(registry.features)
            registry.metadata.last_updated = datetime.now().isoformat()

            save_features(registry, root)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "featureAdded",
                {
                    "id": feature_id,
                    "description": new_feature.description,
                    "category": new_feature.category,
                    "status": new_feature.status.value,
                },
            )

            return {
                "success": True,
                "feature": new_feature.to_dict(),
                "message": f"Created feature {feature_id}",
            }
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.put("/api/features/{feature_id}")
    async def api_feature_update(
        feature_id: str,
        update_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update an existing feature.

        Path Parameters:
            feature_id: Feature ID (e.g., F001)

        Request Body:
            Any Feature properties to update (description, category, priority, etc.)

        Returns:
            Updated feature or 404 error.
        """
        from datetime import datetime

        from ..data import load_features, save_features
        from ..models import FeatureStatus

        try:
            registry = load_features(root)
            registry._build_index()

            if feature_id not in registry._feature_index:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail=f"Feature not found: {feature_id}")

            feature = registry._feature_index[feature_id]

            # Update allowed fields
            if "description" in update_data and update_data["description"]:
                feature.description = update_data["description"]
            elif "description" in update_data and not update_data["description"]:
                from fastapi import HTTPException

                raise HTTPException(status_code=400, detail="Description cannot be empty")

            if "category" in update_data:
                feature.category = update_data["category"]

            if "priority" in update_data:
                priority = update_data["priority"]
                if not isinstance(priority, int) or priority < 1 or priority > 5:
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400,
                        detail="Priority must be an integer between 1 and 5",
                    )
                feature.priority = priority

            if "acceptance_criteria" in update_data:
                feature.acceptance_criteria = update_data["acceptance_criteria"]

            if "notes" in update_data:
                feature.notes = update_data["notes"]

            if "dependencies" in update_data:
                feature.dependencies = update_data["dependencies"]

            if "status" in update_data:
                try:
                    feature.status = FeatureStatus(update_data["status"])
                except ValueError:
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid status: {update_data['status']}",
                    ) from None

            if "blocked_by" in update_data:
                feature.blocked_by = update_data["blocked_by"]

            if "estimated_effort" in update_data:
                feature.estimated_effort = update_data["estimated_effort"]

            # Update metadata
            feature.last_worked_on = datetime.now().isoformat()
            registry.metadata.last_updated = datetime.now().isoformat()

            save_features(registry, root)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "featureUpdated",
                {
                    "id": feature_id,
                    "description": feature.description,
                    "category": feature.category,
                    "status": feature.status.value,
                },
            )

            return {
                "success": True,
                "feature": feature.to_dict(),
                "message": f"Updated feature {feature_id}",
            }
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.post("/api/features/{feature_id}/start")
    async def api_feature_start(feature_id: str) -> dict[str, Any]:
        """Mark feature as in-progress.

        Path Parameters:
            feature_id: Feature ID (e.g., F001)

        Returns:
            Updated feature or 404 error.
            Includes warning if other features are in-progress.
        """
        from datetime import datetime

        from ..data import load_features, load_progress, save_features, save_progress
        from ..models import FeatureStatus

        try:
            registry = load_features(root)
            registry._build_index()

            if feature_id not in registry._feature_index:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail=f"Feature not found: {feature_id}")

            feature = registry._feature_index[feature_id]

            # Check for other in-progress features
            in_progress = [f for f in registry.features if f.status == FeatureStatus.IN_PROGRESS]
            warning = None
            if in_progress and feature_id not in [f.id for f in in_progress]:
                warning = f"Other features are in-progress: {', '.join(f.id for f in in_progress)}"

            # Update feature status
            feature.status = FeatureStatus.IN_PROGRESS
            feature.last_worked_on = datetime.now().isoformat()
            registry.metadata.last_updated = datetime.now().isoformat()

            save_features(registry, root)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "featureUpdated",
                {
                    "id": feature_id,
                    "status": "in-progress",
                    "action": "started",
                },
            )

            # Update progress
            try:
                from ..data import regenerate_progress_md, update_quick_reference

                progress = load_progress(root)
                update_quick_reference(progress, registry)
                save_progress(progress, root)
                regenerate_progress_md(root)
            except Exception:
                pass  # Progress update is optional

            result = {
                "success": True,
                "feature": feature.to_dict(),
                "message": f"Started feature {feature_id}",
            }
            if warning:
                result["warning"] = warning

            return result
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.post("/api/features/{feature_id}/verify")
    async def api_feature_verify(
        feature_id: str,
        verify_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Mark feature as verified with evidence.

        Path Parameters:
            feature_id: Feature ID (e.g., F001)

        Request Body:
            {
                "evidence": str (required) - Evidence links/description (comma-separated)
            }

        Returns:
            Updated feature or 404/400 error.
        """
        from datetime import datetime

        from ..data import (
            load_config,
            load_features,
            load_progress,
            save_features,
            save_progress,
        )
        from ..models import FeatureStatus
        from ..validation import sanitize_string

        try:
            # Validate evidence
            evidence = verify_data.get("evidence", "")
            if not evidence:
                from fastapi import HTTPException

                raise HTTPException(status_code=400, detail="Evidence is required for verification")

            # Sanitize evidence
            evidence = sanitize_string(evidence)
            if not evidence:
                from fastapi import HTTPException

                raise HTTPException(status_code=400, detail="Evidence cannot be empty")

            registry = load_features(root)
            registry._build_index()

            if feature_id not in registry._feature_index:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail=f"Feature not found: {feature_id}")

            feature = registry._feature_index[feature_id]
            config = load_config(root)

            # Parse evidence paths
            evidence_paths = [
                sanitize_string(p.strip()) or "" for p in evidence.split(",") if p.strip()
            ]

            # Update feature status
            feature.status = FeatureStatus.VERIFIED
            feature.passes = True
            feature.verified_at = datetime.now().isoformat()
            feature.verified_by = config.verified_by
            feature.evidence_links = evidence_paths

            # Update metadata
            registry.update_metadata()
            registry.metadata.last_updated = datetime.now().isoformat()

            save_features(registry, root)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "featureUpdated",
                {
                    "id": feature_id,
                    "status": "verified",
                    "action": "verified",
                    "passes": True,
                },
            )

            # Update progress
            try:
                from ..data import regenerate_progress_md, update_quick_reference

                progress = load_progress(root)
                update_quick_reference(progress, registry)
                save_progress(progress, root)
                regenerate_progress_md(root)
            except Exception:
                pass  # Progress update is optional

            return {
                "success": True,
                "feature": feature.to_dict(),
                "message": f"Verified feature {feature_id}",
                "evidence": evidence_paths,
            }
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.post("/api/features/{feature_id}/block")
    async def api_feature_block(
        feature_id: str,
        block_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Mark feature as blocked with reason.

        Path Parameters:
            feature_id: Feature ID (e.g., F001)

        Request Body:
            {
                "reason": str (required) - Reason for blocking
            }

        Returns:
            Updated feature or 404/400 error.
        """
        from datetime import datetime

        from ..data import load_features, load_progress, save_features, save_progress
        from ..models import FeatureStatus
        from ..validation import sanitize_string

        try:
            # Validate reason
            reason = block_data.get("reason", "")
            if not reason:
                from fastapi import HTTPException

                raise HTTPException(status_code=400, detail="Reason is required for blocking")

            # Sanitize reason
            reason = sanitize_string(reason)
            if not reason:
                from fastapi import HTTPException

                raise HTTPException(status_code=400, detail="Reason cannot be empty")

            registry = load_features(root)
            registry._build_index()

            if feature_id not in registry._feature_index:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail=f"Feature not found: {feature_id}")

            feature = registry._feature_index[feature_id]

            # Update feature status
            feature.status = FeatureStatus.BLOCKED
            feature.blocked_by = reason
            feature.last_worked_on = datetime.now().isoformat()
            registry.metadata.last_updated = datetime.now().isoformat()

            save_features(registry, root)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "featureUpdated",
                {
                    "id": feature_id,
                    "status": "blocked",
                    "action": "blocked",
                    "reason": reason,
                },
            )

            # Update progress
            try:
                from ..data import regenerate_progress_md, update_quick_reference

                progress = load_progress(root)
                update_quick_reference(progress, registry)
                save_progress(progress, root)
                regenerate_progress_md(root)
            except Exception:
                pass  # Progress update is optional

            return {
                "success": True,
                "feature": feature.to_dict(),
                "message": f"Blocked feature {feature_id}",
                "reason": reason,
            }
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.post("/api/features/reorder")
    async def api_features_reorder(reorder_data: dict[str, Any]) -> dict[str, Any]:
        """Reorder features by updating their priorities.

        Request Body:
            {
                "order": [
                    {"id": "F001", "priority": 1},
                    {"id": "F002", "priority": 2},
                    ...
                ]
            }

        Returns:
            Success status and count of updated features.
        """
        from datetime import datetime

        from ..data import load_features, save_features

        try:
            order = reorder_data.get("order", [])
            if not order:
                from fastapi import HTTPException

                raise HTTPException(status_code=400, detail="Order list is required")

            registry = load_features(root)
            registry._build_index()

            updated_count = 0
            for item in order:
                feature_id = item.get("id")
                priority = item.get("priority")

                if not feature_id or priority is None:
                    continue

                if feature_id in registry._feature_index:
                    feature = registry._feature_index[feature_id]
                    # Validate priority
                    if isinstance(priority, int) and 1 <= priority <= 5:
                        if feature.priority != priority:
                            feature.priority = priority
                            updated_count += 1

            # Update metadata
            registry.metadata.last_updated = datetime.now().isoformat()
            save_features(registry, root)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "featuresReordered",
                {
                    "updated_count": updated_count,
                },
            )

            return {
                "success": True,
                "message": f"Reordered {updated_count} features",
                "updated_count": updated_count,
            }
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.get("/api/progress")
    async def api_progress() -> dict[str, Any]:
        """Get all session history.

        Returns:
            ProgressLog with all session history.
        """
        from ..data import load_progress

        try:
            progress = load_progress(root)
            return {
                "sessions": [s.to_dict() for s in progress.sessions],
                "current_status": progress.current_status,
                "total_sessions": len(progress.sessions),
            }
        except Exception as e:
            return {"error": str(e)}

    @app_instance.get("/api/commits")
    async def api_commits(count: int = 10) -> list[dict[str, Any]]:
        """Get recent git commits.

        Args:
            count: Number of commits to return (default 10)

        Returns:
            List of commit objects with hash, author, date, and message.
            Returns empty list if not a git repo or any other error.
        """
        from ..git import get_recent_commits

        try:
            commits = get_recent_commits(count=count, path=root)
            return [
                {
                    "hash": commit.hash,
                    "author": commit.author,
                    "date": commit.date,
                    "message": commit.message,
                }
                for commit in commits
            ]
        except Exception:
            # Return empty list if not a git repo or any other error
            return []

    @app_instance.get("/api/activity")
    async def api_activity(limit: int = 10) -> dict[str, Any]:
        """Get recent activity feed.

        Args:
            limit: Maximum number of activities to return (default 10)

        Returns:
            List of activity objects with type, description, timestamp.
        """
        from ..data import load_features, load_progress
        from ..git import get_recent_commits

        try:
            activities: list[dict[str, Any]] = []

            # Get recent feature updates
            registry = load_features(root)
            for feature in sorted(
                registry.features, key=lambda f: f.last_worked_on or "", reverse=True
            )[:limit]:
                if feature.last_worked_on:
                    activity_type = (
                        "feature_verified"
                        if feature.status.value == "verified"
                        else (
                            "feature_started"
                            if feature.status.value == "in-progress"
                            else "feature_blocked"
                            if feature.status.value == "blocked"
                            else "feature_updated"
                        )
                    )
                    activities.append(
                        {
                            "id": f"{feature.id}_{feature.last_worked_on}",
                            "type": activity_type,
                            "featureId": feature.id,
                            "description": feature.description,
                            "timestamp": feature.last_worked_on,
                        }
                    )

            # Get recent sessions
            progress = load_progress(root)
            for session in reversed(progress.sessions[-limit:]):
                activities.append(
                    {
                        "id": f"session_{session.session_number}",
                        "type": "session_started",
                        "description": session.focus,
                        "timestamp": f"{session.date}T00:00:00",
                    }
                )

            # Get recent commits
            try:
                commits = get_recent_commits(count=limit, path=root)
                for commit in commits:
                    activities.append(
                        {
                            "id": f"commit_{commit.hash}",
                            "type": "commit",
                            "description": commit.message,
                            "timestamp": commit.date,
                            "metadata": {
                                "hash": commit.short_hash,
                                "author": commit.author,
                            },
                        }
                    )
            except Exception:
                pass  # Ignore git errors

            # Sort by timestamp and limit
            activities.sort(key=lambda a: a["timestamp"], reverse=True)
            activities = activities[:limit]

            return {"activities": activities}
        except Exception as e:
            return {"activities": [], "error": str(e)}

    @app_instance.get("/api/config")
    async def api_config_get() -> dict[str, Any]:
        """Get current configuration.

        Returns:
            Configuration settings including:
            - default_category: Default category for new features
            - default_priority: Default priority for new features (1-5)
            - verified_by: Identifier for verification field
            - progress_output_path: Path for generated progress file
            - auto_regenerate_progress: Whether to auto-regenerate progress
            - prd_source: Link to PRD document (optional)
            - klondike_version: Version of klondike that created config
            - configured_agents: List of configured AI agents
        """
        from ..data import load_config

        try:
            config = load_config(root)
            return config.to_dict()
        except Exception as e:
            return {"error": str(e)}

    @app_instance.put("/api/config")
    async def api_config_update(config_data: dict[str, Any]) -> dict[str, Any]:
        """Update configuration.

        Request Body:
            Partial or complete config object with fields to update:
            - default_category: str (any category name)
            - default_priority: int (1-5, 1=critical)
            - verified_by: str
            - progress_output_path: str
            - auto_regenerate_progress: bool
            - prd_source: str (optional)
            - configured_agents: list[str]

        Returns:
            Updated configuration or validation error.
        """
        from ..data import get_klondike_dir, load_config

        try:
            # Load current config
            config = load_config(root)

            # Validate and apply updates
            if "default_priority" in config_data:
                priority = config_data["default_priority"]
                if not isinstance(priority, int) or not (1 <= priority <= 5):
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400,
                        detail="default_priority must be an integer between 1 and 5",
                    )
                config.default_priority = priority

            if "default_category" in config_data:
                category = config_data["default_category"]
                if not isinstance(category, str) or not category.strip():
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400,
                        detail="default_category must be a non-empty string",
                    )
                config.default_category = category.strip()

            if "verified_by" in config_data:
                verified_by = config_data["verified_by"]
                if not isinstance(verified_by, str) or not verified_by.strip():
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400, detail="verified_by must be a non-empty string"
                    )
                config.verified_by = verified_by.strip()

            if "progress_output_path" in config_data:
                output_path = config_data["progress_output_path"]
                if not isinstance(output_path, str) or not output_path.strip():
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400,
                        detail="progress_output_path must be a non-empty string",
                    )
                config.progress_output_path = output_path.strip()

            if "auto_regenerate_progress" in config_data:
                auto_regen = config_data["auto_regenerate_progress"]
                if not isinstance(auto_regen, bool):
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400,
                        detail="auto_regenerate_progress must be a boolean",
                    )
                config.auto_regenerate_progress = auto_regen

            if "prd_source" in config_data:
                prd_source = config_data["prd_source"]
                if prd_source is not None and not isinstance(prd_source, str):
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400, detail="prd_source must be a string or null"
                    )
                config.prd_source = prd_source.strip() if prd_source else None

            if "configured_agents" in config_data:
                agents = config_data["configured_agents"]
                if not isinstance(agents, list) or not all(isinstance(a, str) for a in agents):
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=400,
                        detail="configured_agents must be a list of strings",
                    )
                config.configured_agents = [a.strip() for a in agents if a.strip()]

            # Save updated config
            klondike_dir = get_klondike_dir(root)
            config_path = klondike_dir / "config.yaml"
            config.save(config_path)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "configChanged",
                {
                    "updated": list(config_data.keys()),
                },
            )

            return {
                "success": True,
                "config": config.to_dict(),
                "message": "Configuration updated successfully",
            }

        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.post("/api/session/start")
    async def api_session_start(session_data: dict[str, Any]) -> dict[str, Any]:
        """Start a new session.

        Request Body:
            {
                "focus": str (required) - Session focus/description
            }

        Returns:
            Created session or validation error.
        """
        from datetime import datetime

        from ..data import (
            load_features,
            load_progress,
            regenerate_progress_md,
            save_features,
            save_progress,
        )
        from ..git import get_git_status
        from ..models import Session

        try:
            # Validate focus
            focus = session_data.get("focus", "")
            if not focus:
                from fastapi import HTTPException

                raise HTTPException(status_code=400, detail="Focus is required")

            registry = load_features(root)
            progress = load_progress(root)

            # Check if there's already an active session
            current = progress.get_current_session()
            if current and progress.current_status == "In Progress":
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=400,
                    detail=f"Session {current.session_number} is already active. End it first.",
                )

            # Validate artifact integrity
            actual_total = len(registry.features)
            actual_passing = sum(1 for f in registry.features if f.passes)

            warnings = []
            if registry.metadata.total_features != actual_total:
                warnings.append(
                    f"metadata.totalFeatures ({registry.metadata.total_features}) != actual ({actual_total})"
                )
                registry.metadata.total_features = actual_total

            if registry.metadata.passing_features != actual_passing:
                warnings.append(
                    f"metadata.passingFeatures ({registry.metadata.passing_features}) != actual ({actual_passing})"
                )
                registry.metadata.passing_features = actual_passing

            # Get git status
            git_status = get_git_status(root)
            git_info = None
            if git_status.is_git_repo:
                git_info = {
                    "branch": git_status.current_branch,
                    "has_uncommitted": git_status.has_uncommitted_changes,
                }

            # Create new session
            session_num = progress.next_session_number()
            new_session = Session(
                session_number=session_num,
                date=datetime.now().strftime("%Y-%m-%d"),
                agent="Coding Agent",
                duration="(in progress)",
                focus=focus,
                completed=[],
                in_progress=["Session started"],
                blockers=[],
                next_steps=[],
                technical_notes=[],
            )

            progress.add_session(new_session)
            progress.current_status = "In Progress"

            # Save changes
            from ..data import update_quick_reference

            update_quick_reference(progress, registry)
            save_features(registry, root)
            save_progress(progress, root)
            regenerate_progress_md(root)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "sessionStarted",
                {
                    "sessionNumber": new_session.session_number,
                    "focus": new_session.focus,
                },
            )

            # Build response
            result = {
                "success": True,
                "session": new_session.to_dict(),
                "project_status": {
                    "total": registry.metadata.total_features,
                    "passing": registry.metadata.passing_features,
                    "percent": (
                        round(
                            registry.metadata.passing_features
                            / registry.metadata.total_features
                            * 100,
                            1,
                        )
                        if registry.metadata.total_features > 0
                        else 0
                    ),
                },
                "message": f"Session {session_num} started",
            }

            if warnings:
                result["warnings"] = warnings
            if git_info:
                result["git"] = git_info

            return result
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.post("/api/session/end")
    async def api_session_end(end_data: dict[str, Any]) -> dict[str, Any]:
        """End the current session.

        Request Body:
            {
                "summary": str (optional) - Session summary
                "completed": list[str] (optional) - Completed items
                "blockers": list[str] (optional) - Blockers encountered
                "nextSteps": list[str] (optional) - Next steps (auto-generated if not provided)
            }

        Returns:
            Updated session or error if no active session.
        """
        from ..data import (
            load_features,
            load_progress,
            regenerate_progress_md,
            save_progress,
        )

        try:
            registry = load_features(root)
            progress = load_progress(root)

            current = progress.get_current_session()
            if not current or progress.current_status != "In Progress":
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=400,
                    detail="No active session found. Start a session first.",
                )

            # Update session
            current.duration = "~session"  # TODO: Calculate actual duration
            current.in_progress = []

            if "summary" in end_data and end_data["summary"]:
                current.focus = end_data["summary"]

            if "completed" in end_data:
                current.completed = end_data["completed"]

            if "blockers" in end_data:
                current.blockers = end_data["blockers"]

            if "nextSteps" in end_data:
                current.next_steps = end_data["nextSteps"]
            else:
                # Auto-generate next steps from priority features
                priority = registry.get_priority_features(3)
                current.next_steps = [f"Continue {f.id}: {f.description}" for f in priority]

            progress.current_status = "Session Ended"

            # Save changes
            from ..data import update_quick_reference

            update_quick_reference(progress, registry)
            save_progress(progress, root)
            regenerate_progress_md(root)

            # Broadcast event to WebSocket clients
            await manager.broadcast(
                "sessionEnded",
                {
                    "sessionNumber": current.session_number,
                    "focus": current.focus,
                },
            )

            return {
                "success": True,
                "session": current.to_dict(),
                "message": f"Session {current.session_number} ended",
            }
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return {"error": str(e)}

    @app_instance.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_spa(full_path: str) -> Response:
        """Serve index.html for all routes (React Router support)."""
        # Serve static files directly if they exist
        static_file = static_dir / full_path
        if static_file.is_file():
            return FileResponse(static_file)

        # Otherwise serve index.html for client-side routing
        index_path = static_dir / "index.html"
        if not index_path.exists():
            return HTMLResponse(
                content="<h1>Klondike Spec CLI</h1><p>Static files not found</p>",
                status_code=500,
            )
        return FileResponse(index_path)

    # Suppress Windows ConnectionResetError in asyncio logs
    class WindowsConnectionFilter(logging.Filter):
        """Filter to suppress Windows ConnectionResetError in asyncio."""

        def filter(self, record: logging.LogRecord) -> bool:
            # Suppress the Windows-specific connection reset errors
            if "ConnectionResetError" in record.getMessage():
                return False
            if "forcibly closed by the remote host" in record.getMessage():
                return False
            return True

    # Apply filter to asyncio logger
    asyncio_logger = logging.getLogger("asyncio")
    asyncio_logger.addFilter(WindowsConnectionFilter())

    # Print startup message
    echo("")
    echo("♠️  Starting Klondike Spec Web UI")
    echo("=" * 50)
    echo(f"   Project: {root.name}")
    echo(f"   URL:     http://{host}:{port}")
    echo(f"   Version: {__version__}")
    echo("")
    echo("Press Ctrl+C to stop the server")
    echo("")

    # Open browser after a short delay to ensure server is ready
    if open_browser:

        def open_browser_delayed() -> None:
            import time

            time.sleep(1.5)  # Wait for server to be ready
            url = f"http://{host}:{port}"
            webbrowser.open(url)

        browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
        browser_thread.start()

    # Configure uvicorn for better Windows support
    # Handle Ctrl+C gracefully on Windows
    shutdown_event = False

    def handle_shutdown(signum: int, frame: FrameType | None) -> None:
        nonlocal shutdown_event
        shutdown_event = True
        echo("\n♠️  Server stopped")
        observer.stop()
        # Cancel pending asyncio tasks
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if loop and loop.is_running():
                # Get all tasks
                tasks = [t for t in asyncio.all_tasks(loop) if not t.done()]
                for task in tasks:
                    task.cancel()
        except Exception:
            pass  # Ignore errors during cleanup
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    if hasattr(signal, "SIGBREAK"):  # Windows-specific
        signal.signal(signal.SIGBREAK, handle_shutdown)

    # Start server
    try:
        # On Windows, use different configuration to avoid asyncio issues
        import uvicorn

        config = uvicorn.Config(
            app_instance,
            host=host,
            port=port,
            log_level="info",
            loop="asyncio",
        )
        server = uvicorn.Server(config)
        server.run()
    except OSError as err:
        if "address already in use" in str(err).lower():
            raise PithException(
                f"Port {port} is already in use.\n"
                f"Try a different port: klondike serve --port {port + 1}"
            ) from err
        raise
    except KeyboardInterrupt:
        echo("\n♠️  Server stopped")
    finally:
        # Cleanup file watcher
        try:
            observer.stop()
            observer.join(timeout=2.0)
        except Exception:
            pass  # Ignore cleanup errors
        # Cancel any remaining asyncio tasks
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if loop:
                tasks = [t for t in asyncio.all_tasks(loop) if not t.done()]
                for task in tasks:
                    task.cancel()
                # Give tasks a moment to cancel
                if tasks:
                    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        except Exception:
            pass  # Ignore errors during cleanup
