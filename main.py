import os
import pwd
import json
import shutil
import decky
import asyncio
from pathlib import Path

# Get Decky environment variables with fallbacks
DECKY_USER = os.environ.get("DECKY_USER", "deck")
DECKY_USER_HOME = os.environ.get("DECKY_USER_HOME", "/home/deck")

# Get UID from username using pwd module
try:
    DECKY_USER_UID = pwd.getpwnam(DECKY_USER).pw_uid
except KeyError:
    DECKY_USER_UID = 1000  # fallback to default deck UID

# Plugin configuration using Decky's environment
LIBRESPOT_BIN = f"{DECKY_USER_HOME}/librespot"
LIBRESPOT_SPEAKER_NAME = "decky-spotify"
SERVICE_NAME = "decky-librespot.service"
SYSTEMD_USER_DIR = Path(DECKY_USER_HOME) / ".config" / "systemd" / "user"

# Event handling configuration
DATA_DIR = Path(DECKY_USER_HOME) / ".local" / "share" / "decky-spotify"
SOCKET_PATH = DATA_DIR / "event.sock"
EVENT_HANDLER_SRC = Path(__file__).parent / "event_handler.py"
EVENT_HANDLER_DEST = DATA_DIR / "event_handler.py"

class Plugin:
    def __init__(self):
        self._now_playing = {
            "connected": False,
            "user_name": None,
            "connection_id": None,
            "track": None,
            "playback_state": "stopped",
            "position_ms": 0
        }
        self._socket_server = None

    def _get_service_content(self):
        """Generate systemd service file content"""
        return f"""[Unit]
Description=Librespot Spotify Connect Speaker
Wants=network.target sound.target
After=network.target sound.target

[Service]
Type=simple
ExecStart={LIBRESPOT_BIN} -n "{LIBRESPOT_SPEAKER_NAME}" -b 320 --onevent {EVENT_HANDLER_DEST}
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
"""

    def _create_service_file(self):
        """Create systemd service file"""
        try:
            # Create systemd user directory if it doesn't exist
            SYSTEMD_USER_DIR.mkdir(parents=True, exist_ok=True)

            service_path = SYSTEMD_USER_DIR / SERVICE_NAME

            # Write service file
            with open(service_path, 'w') as f:
                f.write(self._get_service_content())

            decky.logger.info(f"Created service file at {service_path}")
            return True

        except Exception as e:
            decky.logger.error(f"Failed to create service file: {e}", exc_info=True)
            return False

    def _get_user_env(self):
        """Get environment for running user commands outside Decky sandbox"""
        env = os.environ.copy()

        # Clear LD_LIBRARY_PATH to avoid Decky's sandboxed libraries
        # conflicting with system binaries like systemctl
        env.pop("LD_LIBRARY_PATH", None)
        env.pop("LD_PRELOAD", None)

        # Decky runs as a system service, so user session variables may be missing
        # Set them explicitly using the UID derived from DECKY_USER
        if "XDG_RUNTIME_DIR" not in env:
            env["XDG_RUNTIME_DIR"] = f"/run/user/{DECKY_USER_UID}"
        if "DBUS_SESSION_BUS_ADDRESS" not in env:
            env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path=/run/user/{DECKY_USER_UID}/bus"

        return env

    def _deploy_event_handler(self):
        """Copy event_handler.py to user data directory"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy(EVENT_HANDLER_SRC, EVENT_HANDLER_DEST)
            os.chmod(EVENT_HANDLER_DEST, 0o755)
            decky.logger.info(f"Deployed event handler to {EVENT_HANDLER_DEST}")
            return True
        except Exception as e:
            decky.logger.error(f"Failed to deploy event handler: {e}", exc_info=True)
            return False

    async def _start_socket_server(self):
        """Start Unix socket server to receive events from event_handler.py"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)

            # Remove existing socket if present
            if SOCKET_PATH.exists():
                SOCKET_PATH.unlink()

            server = await asyncio.start_unix_server(
                self._handle_event_connection,
                path=str(SOCKET_PATH)
            )
            # Allow event handler (running as user) to connect
            os.chmod(SOCKET_PATH, 0o666)
            self._socket_server = server
            decky.logger.info(f"Socket server started at {SOCKET_PATH}")

        except Exception as e:
            decky.logger.error(f"Failed to start socket server: {e}", exc_info=True)

    async def _stop_socket_server(self):
        """Stop the Unix socket server"""
        if self._socket_server:
            self._socket_server.close()
            await self._socket_server.wait_closed()
            self._socket_server = None
            decky.logger.info("Socket server stopped")

        # Clean up socket file
        if SOCKET_PATH.exists():
            try:
                SOCKET_PATH.unlink()
            except Exception:
                pass

    async def _handle_event_connection(self, reader, writer):
        """Handle incoming event from event_handler.py"""
        try:
            data = await reader.read(4096)
            writer.close()
            await writer.wait_closed()

            if data:
                event = json.loads(data.decode())
                self._process_event(event)
        except Exception as e:
            decky.logger.error(f"Error handling event connection: {e}")

    def _process_event(self, event):
        """Update internal state based on librespot event"""
        event_type = event.get("event")
        decky.logger.info(f"Received event: {event_type}")

        if event_type == "session_connected":
            self._now_playing["connected"] = True
            self._now_playing["user_name"] = event.get("user_name")
            self._now_playing["connection_id"] = event.get("connection_id")

        elif event_type == "session_disconnected":
            self._now_playing["connected"] = False
            self._now_playing["user_name"] = None
            self._now_playing["connection_id"] = None
            self._now_playing["track"] = None
            self._now_playing["playback_state"] = "stopped"

        elif event_type == "track_changed":
            self._now_playing["track"] = {
                "name": event.get("name"),
                "artists": event.get("artists", []),
                "album": event.get("album"),
                "cover_url": event.get("cover_url"),
                "duration_ms": event.get("duration_ms", 0)
            }

        elif event_type in ("playing", "paused", "stopped"):
            self._now_playing["playback_state"] = event_type
            self._now_playing["position_ms"] = event.get("position_ms", 0)

        # Emit event to frontend for real-time updates
        asyncio.create_task(decky.emit("now_playing", self._now_playing))

    async def _run_systemctl(self, *args):
        """Run a systemctl --user command"""
        try:
            cmd = ["systemctl", "--user"] + list(args)
            decky.logger.info(f"Running: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_user_env()
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                decky.logger.error(f"systemctl command failed: {stderr.decode()}")
                return False, stdout.decode(), stderr.decode()

            return True, stdout.decode(), stderr.decode()

        except Exception as e:
            decky.logger.error(f"Failed to run systemctl: {e}", exc_info=True)
            return False, "", str(e)

    async def _reload_daemon(self):
        """Reload systemd daemon"""
        success, _, _ = await self._run_systemctl("daemon-reload")
        if success:
            decky.logger.info("Systemd daemon reloaded")
        return success

    async def start_librespot(self):
        """Start librespot service"""
        try:
            # Check if binary exists
            if not os.path.exists(LIBRESPOT_BIN):
                decky.logger.error(f"Librespot binary not found at {LIBRESPOT_BIN}")
                return False

            # Make sure it's executable
            if not os.access(LIBRESPOT_BIN, os.X_OK):
                decky.logger.warning(f"Making {LIBRESPOT_BIN} executable")
                os.chmod(LIBRESPOT_BIN, 0o755)

            decky.logger.info("Starting librespot service...")
            success, _, _ = await self._run_systemctl("start", SERVICE_NAME)

            if success:
                decky.logger.info("Librespot service started successfully")
            return success

        except Exception as e:
            decky.logger.error(f"Failed to start librespot: {e}", exc_info=True)
            return False

    async def stop_librespot(self):
        """Stop the librespot service"""
        try:
            decky.logger.info("Stopping librespot service...")
            success, _, _ = await self._run_systemctl("stop", SERVICE_NAME)

            if success:
                decky.logger.info("Librespot service stopped successfully")
            return success

        except Exception as e:
            decky.logger.error(f"Error stopping librespot: {e}", exc_info=True)
            return False

    async def enable_librespot(self):
        """Enable librespot service to start on boot"""
        try:
            decky.logger.info("Enabling librespot service for auto-start...")
            success, _, _ = await self._run_systemctl("enable", SERVICE_NAME)

            if success:
                decky.logger.info("Librespot service enabled successfully")
            return success

        except Exception as e:
            decky.logger.error(f"Error enabling librespot: {e}", exc_info=True)
            return False

    async def disable_librespot(self):
        """Disable librespot service from starting on boot"""
        try:
            decky.logger.info("Disabling librespot service auto-start...")
            success, _, _ = await self._run_systemctl("disable", SERVICE_NAME)

            if success:
                decky.logger.info("Librespot service disabled successfully")
            return success

        except Exception as e:
            decky.logger.error(f"Error disabling librespot: {e}", exc_info=True)
            return False

    async def get_status(self):
        """Get the status of librespot service - callable from frontend"""
        try:
            # Check if service is active
            success, stdout, _ = await self._run_systemctl("is-active", SERVICE_NAME)
            is_active = stdout.strip() == "active"

            # Check if service is enabled
            success, stdout, _ = await self._run_systemctl("is-enabled", SERVICE_NAME)
            is_enabled = stdout.strip() == "enabled"

            # Get detailed state
            _, stdout, _ = await self._run_systemctl("show", SERVICE_NAME, "--property=ActiveState", "--value")
            state = stdout.strip() or "unknown"

            return {
                "running": is_active,
                "enabled": is_enabled,
                "service": SERVICE_NAME,
                "state": state
            }

        except Exception as e:
            decky.logger.error(f"Error getting status: {e}", exc_info=True)
            return {"running": False, "enabled": False, "service": SERVICE_NAME, "state": "error"}

    async def restart_librespot(self):
        """Restart librespot service - callable from frontend"""
        try:
            decky.logger.info("Restarting librespot service...")
            success, _, _ = await self._run_systemctl("restart", SERVICE_NAME)

            if success:
                decky.logger.info("Librespot service restarted successfully")
            return success

        except Exception as e:
            decky.logger.error(f"Error restarting librespot: {e}", exc_info=True)
            return False

    async def get_logs(self, lines=50):
        """Get recent logs from the service - callable from frontend"""
        try:
            # Input validation: ensure lines is a positive integer within reasonable bounds
            try:
                lines = int(lines)
            except (ValueError, TypeError):
                lines = 50
            lines = max(1, min(lines, 1000))

            process = await asyncio.create_subprocess_exec(
                "journalctl", "--user", "-u", SERVICE_NAME, "-n", str(lines), "--no-pager",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_user_env()
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return stdout.decode()
            else:
                decky.logger.error(f"Failed to get logs: {stderr.decode()}")
                return None

        except Exception as e:
            decky.logger.error(f"Error getting logs: {e}")
            return None

    async def get_now_playing(self):
        """Get current playback state - callable from frontend"""
        return self._now_playing

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        try:
            decky.logger.info("Starting librespot plugin")

            # Deploy event handler script
            if not self._deploy_event_handler():
                decky.logger.error("Failed to deploy event handler")
                return

            # Start socket server to receive events
            await self._start_socket_server()

            # Create/update systemd service file
            if not self._create_service_file():
                decky.logger.error("Failed to setup systemd service")
                return

            # Reload daemon to pick up new/updated service file
            await self._reload_daemon()

            # Check current status
            status = await self.get_status()
            decky.logger.info(f"Current status: {status}")

            # Start the service if not already running
            if not status["running"]:
                success = await self.start_librespot()

                if success:
                    # Wait a moment and check status again
                    await asyncio.sleep(1)
                    status = await self.get_status()
                    decky.logger.info(f"Plugin loaded successfully. Status: {status}")
                else:
                    decky.logger.error("Failed to start librespot service")
            else:
                decky.logger.info("Librespot service already running")

        except Exception as e:
            decky.logger.error(f"Error in _main: {e}", exc_info=True)

    # Function called first during the unload process
    async def _unload(self):
        decky.logger.info("Unloading plugin")
        # Stop the socket server
        await self._stop_socket_server()
        # Don't stop the service on unload - let it keep running
        # Users can manually stop it if they want

    # Function called after `_unload` during uninstall
    async def _uninstall(self):
        decky.logger.info("Uninstalling plugin")

        # Stop and disable the service
        await self.stop_librespot()
        await self.disable_librespot()

        # Remove service file
        try:
            service_path = SYSTEMD_USER_DIR / SERVICE_NAME
            if service_path.exists():
                service_path.unlink()
                decky.logger.info(f"Removed service file: {service_path}")

            # Reload systemd
            await self._reload_daemon()

        except Exception as e:
            decky.logger.error(f"Error removing service file: {e}")

        # Clean up event handler and socket
        try:
            if EVENT_HANDLER_DEST.exists():
                EVENT_HANDLER_DEST.unlink()
                decky.logger.info(f"Removed event handler: {EVENT_HANDLER_DEST}")
            if SOCKET_PATH.exists():
                SOCKET_PATH.unlink()
        except Exception as e:
            decky.logger.error(f"Error cleaning up event files: {e}")

    async def _migration(self):
        decky.logger.info("Migrating")
        # Recreate service file in case it needs updating
        self._create_service_file()
        # Reload daemon
        await self._reload_daemon()
