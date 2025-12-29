"""
Systemd service management for spotifyd.
"""
import os
import asyncio
import decky

from constants import (
    DECKY_USER_UID, SPOTIFYD_BIN, SERVICE_NAME
)


class ServiceManager:
    """Manages the spotifyd systemd user service."""

    def _get_user_env(self):
        """Get environment for running user commands outside Decky sandbox."""
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

    async def _run_systemctl(self, *args):
        """Run a systemctl --user command."""
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

    async def reload_daemon(self):
        """Reload systemd daemon."""
        success, _, _ = await self._run_systemctl("daemon-reload")
        if success:
            decky.logger.info("Systemd daemon reloaded")
        return success

    async def start(self):
        """Start spotifyd service."""
        try:
            # Check if binary exists
            if not os.path.exists(SPOTIFYD_BIN):
                decky.logger.error(f"Spotifyd binary not found at {SPOTIFYD_BIN}")
                return False

            # Make sure it's executable
            if not os.access(SPOTIFYD_BIN, os.X_OK):
                decky.logger.warning(f"Making {SPOTIFYD_BIN} executable")
                os.chmod(SPOTIFYD_BIN, 0o755)

            decky.logger.info("Starting spotifyd service...")
            success, _, _ = await self._run_systemctl("start", SERVICE_NAME)

            if success:
                decky.logger.info("Spotifyd service started successfully")
            return success

        except Exception as e:
            decky.logger.error(f"Failed to start spotifyd: {e}", exc_info=True)
            return False

    async def stop(self):
        """Stop the spotifyd service."""
        try:
            decky.logger.info("Stopping spotifyd service...")
            success, _, _ = await self._run_systemctl("stop", SERVICE_NAME)

            if success:
                decky.logger.info("Spotifyd service stopped successfully")
            return success

        except Exception as e:
            decky.logger.error(f"Error stopping spotifyd: {e}", exc_info=True)
            return False

    async def enable(self):
        """Enable spotifyd service to start on boot."""
        try:
            decky.logger.info("Enabling spotifyd service for auto-start...")
            success, _, _ = await self._run_systemctl("enable", SERVICE_NAME)

            if success:
                decky.logger.info("Spotifyd service enabled successfully")
            return success

        except Exception as e:
            decky.logger.error(f"Error enabling spotifyd: {e}", exc_info=True)
            return False

    async def disable(self):
        """Disable spotifyd service from starting on boot."""
        try:
            decky.logger.info("Disabling spotifyd service auto-start...")
            success, _, _ = await self._run_systemctl("disable", SERVICE_NAME)

            if success:
                decky.logger.info("Spotifyd service disabled successfully")
            return success

        except Exception as e:
            decky.logger.error(f"Error disabling spotifyd: {e}", exc_info=True)
            return False

    async def get_status(self):
        """Get the status of spotifyd service."""
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

    async def restart(self):
        """Restart spotifyd service."""
        try:
            decky.logger.info("Restarting spotifyd service...")
            success, _, _ = await self._run_systemctl("restart", SERVICE_NAME)

            if success:
                decky.logger.info("Spotifyd service restarted successfully")
            return success

        except Exception as e:
            decky.logger.error(f"Error restarting spotifyd: {e}", exc_info=True)
            return False

    async def get_logs(self, lines=50):
        """Get recent logs from the service."""
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
