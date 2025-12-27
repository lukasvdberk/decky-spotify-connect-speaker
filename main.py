import os
import decky
import asyncio
from pathlib import Path

LIBRESPOT_BIN = "/home/deck/librespot"
LIBRESPOT_SPEAKER_NAME = "decky-spotify"
SERVICE_NAME = "decky-librespot.service"
SYSTEMD_USER_DIR = Path.home() / ".config" / "systemd" / "user"

class Plugin:
    def __init__(self):
        pass

    def _get_service_content(self):
        """Generate systemd service file content"""
        return f"""[Unit]
Description=Librespot Spotify Connect Speaker
After=network.target sound.target

[Service]
Type=simple
ExecStart={LIBRESPOT_BIN} -n "{LIBRESPOT_SPEAKER_NAME}" -b 320
Restart=on-failure
RestartSec=5
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
        # Set them explicitly for the deck user (UID 1000)
        if "XDG_RUNTIME_DIR" not in env:
            env["XDG_RUNTIME_DIR"] = "/run/user/1000"
        if "DBUS_SESSION_BUS_ADDRESS" not in env:
            env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/run/user/1000/bus"

        return env

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

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        try:
            decky.logger.info("Starting librespot plugin")

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

    async def _migration(self):
        decky.logger.info("Migrating")
        # Recreate service file in case it needs updating
        self._create_service_file()
        # Reload daemon
        await self._reload_daemon()
