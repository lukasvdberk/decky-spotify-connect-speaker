import os
import pwd
import json
import shutil
import decky
import asyncio
from pathlib import Path
from settings import SettingsManager

# Get Decky environment variables with fallbacks
DECKY_USER = os.environ.get("DECKY_USER", "deck")
DECKY_USER_HOME = os.environ.get("DECKY_USER_HOME", "/home/deck")
SETTINGS_DIR = os.environ.get("DECKY_PLUGIN_SETTINGS_DIR", "")

# Get UID from username using pwd module
try:
    DECKY_USER_UID = pwd.getpwnam(DECKY_USER).pw_uid
except KeyError:
    DECKY_USER_UID = 1000  # fallback to default deck UID

# Plugin configuration using Decky's environment
SPOTIFYD_BIN = f"{DECKY_USER_HOME}/spotifyd"
SERVICE_NAME = "decky-spotifyd.service"
SYSTEMD_USER_DIR = Path(DECKY_USER_HOME) / ".config" / "systemd" / "user"

# MPRIS D-Bus configuration
MPRIS_BUS_NAME_PREFIX = "org.mpris.MediaPlayer2.spotifyd"
MPRIS_OBJECT_PATH = "/org/mpris/MediaPlayer2"
MPRIS_PLAYER_INTERFACE = "org.mpris.MediaPlayer2.Player"

# Event handling configuration
DATA_DIR = Path(DECKY_USER_HOME) / ".local" / "share" / "decky-spotify"
SOCKET_PATH = DATA_DIR / "event.sock"
EVENT_HANDLER_SRC = Path(__file__).parent / "event_handler.py"
EVENT_HANDLER_DEST = DATA_DIR / "event_handler.py"
CONFIG_FILE_PATH = DATA_DIR / "spotifyd.conf"

# Private D-Bus session for MPRIS (no system file modifications needed)
DBUS_CONFIG_FILE = DATA_DIR / "dbus-session.conf"
DBUS_SOCKET_PATH = DATA_DIR / "dbus.sock"
DBUS_ADDRESS_FILE = DATA_DIR / "dbus-address"
WRAPPER_SCRIPT_PATH = DATA_DIR / "spotifyd_wrapper.sh"

# Settings manager initialization
settings = SettingsManager(name="settings", settings_directory=SETTINGS_DIR)
settings.read()

# Default settings
DEFAULT_SETTINGS = {
    "speaker_name": "decky-spotify",
    "bitrate": 320,
    "device_type": "game-console",
    "initial_volume": 80
}

class Plugin:
    def __init__(self):
        self._now_playing = {
            "connected": False,
            "user_name": None,
            "connection_id": None,
            "track": None,
            "playback_state": "stopped",
            "position_ms": 0,
            "volume": 0.5  # 0.0 to 1.0
        }
        self._socket_server = None

    def _get_config_content(self):
        """Generate spotifyd config file content with current settings"""
        speaker_name = settings.getSetting("speaker_name", DEFAULT_SETTINGS["speaker_name"])
        bitrate = settings.getSetting("bitrate", DEFAULT_SETTINGS["bitrate"])
        device_type = settings.getSetting("device_type", DEFAULT_SETTINGS["device_type"])
        initial_volume = settings.getSetting("initial_volume", DEFAULT_SETTINGS["initial_volume"])

        return f"""[global]
# Device name shown in Spotify Connect
device_name = "{speaker_name}"

# Device type shown in Spotify clients
device_type = "{device_type}"

# Audio bitrate: 96, 160 or 320 kbit/s
bitrate = {bitrate}

# Initial volume (0-100)
initial_volume = {initial_volume}

# Enable MPRIS for playback control via D-Bus (using private session bus)
use_mpris = true
dbus_type = "session"

# Event handler script called on playback events
on_song_change_hook = "{EVENT_HANDLER_DEST}"
"""

    def _create_config_file(self):
        """Create spotifyd config file"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE_PATH, 'w') as f:
                f.write(self._get_config_content())
            decky.logger.info(f"Created config file at {CONFIG_FILE_PATH}")
            return True
        except Exception as e:
            decky.logger.error(f"Failed to create config file: {e}", exc_info=True)
            return False

    def _get_dbus_config_content(self):
        """Generate D-Bus session config for private bus"""
        return f"""<!DOCTYPE busconfig PUBLIC
  "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"
  "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <type>session</type>
  <listen>unix:path={DBUS_SOCKET_PATH}</listen>

  <!-- Allow everything - this is a private session bus -->
  <policy context="default">
    <allow send_destination="*"/>
    <allow receive_sender="*"/>
    <allow own="*"/>
    <allow user="*"/>
  </policy>
</busconfig>
"""

    def _get_wrapper_script_content(self):
        """Generate wrapper script that starts private D-Bus and spotifyd"""
        return f"""#!/bin/bash
# Wrapper script to run spotifyd with its own private D-Bus session

# Clean up any existing socket
rm -f "{DBUS_SOCKET_PATH}"

# Start private D-Bus daemon
dbus-daemon --config-file="{DBUS_CONFIG_FILE}" --fork --print-address > "{DBUS_ADDRESS_FILE}"

# Wait for socket to be created and set permissions so root (Decky plugin) can access it
sleep 0.5
chmod 666 "{DBUS_SOCKET_PATH}"

# Read the bus address
export DBUS_SESSION_BUS_ADDRESS=$(cat "{DBUS_ADDRESS_FILE}")

# Cleanup function
cleanup() {{
    # Kill the dbus-daemon when spotifyd exits
    pkill -f "dbus-daemon --config-file={DBUS_CONFIG_FILE}"
    rm -f "{DBUS_SOCKET_PATH}"
}}
trap cleanup EXIT

# Run spotifyd (this blocks until spotifyd exits)
exec {SPOTIFYD_BIN} --no-daemon --config-path {CONFIG_FILE_PATH}
"""

    def _create_dbus_config_file(self):
        """Create D-Bus session config file"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(DBUS_CONFIG_FILE, 'w') as f:
                f.write(self._get_dbus_config_content())
            decky.logger.info(f"Created D-Bus config at {DBUS_CONFIG_FILE}")
            return True
        except Exception as e:
            decky.logger.error(f"Failed to create D-Bus config: {e}", exc_info=True)
            return False

    def _create_wrapper_script(self):
        """Create wrapper script for spotifyd with private D-Bus"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(WRAPPER_SCRIPT_PATH, 'w') as f:
                f.write(self._get_wrapper_script_content())
            os.chmod(WRAPPER_SCRIPT_PATH, 0o755)
            decky.logger.info(f"Created wrapper script at {WRAPPER_SCRIPT_PATH}")
            return True
        except Exception as e:
            decky.logger.error(f"Failed to create wrapper script: {e}", exc_info=True)
            return False

    def _get_service_content(self):
        """Generate systemd service file content"""
        # Use wrapper script that starts private D-Bus session for MPRIS
        return f"""[Unit]
Description=Spotifyd Spotify Connect Speaker
Wants=network.target sound.target
After=network.target sound.target

[Service]
Type=simple
ExecStart={WRAPPER_SCRIPT_PATH}
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

    def _get_mpris_env(self):
        """Get environment for MPRIS dbus-send using private bus address"""
        env = self._get_user_env()

        # Read the bus address from the file written by the wrapper script
        try:
            if DBUS_ADDRESS_FILE.exists():
                bus_address = DBUS_ADDRESS_FILE.read_text().strip()
                if bus_address:
                    env["DBUS_SESSION_BUS_ADDRESS"] = bus_address
                else:
                    decky.logger.warning(f"Bus address file exists but is empty")
            else:
                decky.logger.warning(f"Bus address file does not exist: {DBUS_ADDRESS_FILE}")
        except Exception as e:
            decky.logger.warning(f"Failed to read MPRIS bus address: {e}")

        return env

    async def _get_mpris_bus_name(self):
        """Find the actual MPRIS bus name (includes instance ID)"""
        try:
            # List all names on the bus
            cmd = [
                "dbus-send",
                "--print-reply",
                "--dest=org.freedesktop.DBus",
                "/org/freedesktop/DBus",
                "org.freedesktop.DBus.ListNames"
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_mpris_env()
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                decky.logger.error(f"Failed to list D-Bus names: {stderr.decode()}")
                return None

            # Parse output and find spotifyd MPRIS name
            output = stdout.decode()
            for line in output.split('\n'):
                if MPRIS_BUS_NAME_PREFIX in line and 'string "' in line:
                    # Extract the bus name from: string "org.mpris.MediaPlayer2.spotifyd.instance123"
                    bus_name = line.split('string "')[1].split('"')[0]
                    decky.logger.info(f"Found MPRIS bus name: {bus_name}")
                    return bus_name

            decky.logger.warning(f"No MPRIS bus name found matching {MPRIS_BUS_NAME_PREFIX}")
            return None

        except Exception as e:
            decky.logger.error(f"Failed to get MPRIS bus name: {e}")
            return None

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
        """Update internal state based on spotifyd event"""
        event_type = event.get("event")
        decky.logger.info(f"Received event: {event_type}")

        # Spotifyd track change event
        if event_type == "change":
            self._now_playing["connected"] = True
            track_id = event.get("track_id", "")
            self._now_playing["track"] = {
                "track_id": track_id,
                "duration_ms": event.get("duration_ms", 0)
            }
            self._now_playing["position_ms"] = 0
            # Fetch metadata asynchronously via MPRIS (with delay to let MPRIS initialize)
            asyncio.create_task(self._update_track_metadata_delayed())

        # Spotifyd uses "start" for play event
        elif event_type == "start":
            self._now_playing["connected"] = True
            self._now_playing["playback_state"] = "playing"
            self._now_playing["position_ms"] = event.get("position_ms", 0)

        elif event_type == "pause":
            self._now_playing["playback_state"] = "paused"
            self._now_playing["position_ms"] = event.get("position_ms", 0)

        elif event_type in ("stop", "endoftrack"):
            self._now_playing["playback_state"] = "stopped"
            self._now_playing["position_ms"] = 0

        # Session connected event
        elif event_type == "sessionconnected":
            self._now_playing["connected"] = True

        # Volume changed event
        elif event_type == "volumeset":
            # Fetch current volume from MPRIS
            asyncio.create_task(self._update_volume())

        # Emit event to frontend for real-time updates
        asyncio.create_task(decky.emit("now_playing", self._now_playing))

    async def _update_volume(self):
        """Fetch current volume from MPRIS and update state"""
        volume = await self.get_volume()
        self._now_playing["volume"] = volume
        await decky.emit("now_playing", self._now_playing)

    async def _update_track_metadata_delayed(self):
        """Fetch track metadata with delay to let MPRIS initialize"""
        # Wait a bit for MPRIS to be ready after track change
        await asyncio.sleep(1.0)

        # Retry a few times if MPRIS isn't ready
        for attempt in range(3):
            success = await self._update_track_metadata()
            if success:
                break
            decky.logger.info(f"MPRIS metadata fetch attempt {attempt + 1} failed, retrying...")
            await asyncio.sleep(0.5)

    async def _update_track_metadata(self):
        """Fetch track metadata from MPRIS and update now_playing state"""
        try:
            # Find the actual bus name (includes instance ID)
            bus_name = await self._get_mpris_bus_name()
            if not bus_name:
                decky.logger.error("Could not find MPRIS bus name")
                return False

            decky.logger.info(f"Fetching metadata from {bus_name}")

            # Use dbus-send to get Metadata property from private session bus
            cmd = [
                "dbus-send",
                "--print-reply",
                f"--dest={bus_name}",
                MPRIS_OBJECT_PATH,
                "org.freedesktop.DBus.Properties.Get",
                f"string:{MPRIS_PLAYER_INTERFACE}",
                "string:Metadata"
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_mpris_env()
            )
            stdout, stderr = await process.communicate()

            decky.logger.info(f"Metadata fetch completed with return code: {process.returncode}")

            if process.returncode != 0:
                decky.logger.error(f"Failed to get MPRIS metadata: {stderr.decode()}")
                return False

            # Parse dbus-send output for metadata
            output = stdout.decode()
            track = self._now_playing.get("track", {})

            # Extract title (xesam:title)
            if 'xesam:title' in output:
                title_match = output.split('xesam:title')[1]
                if 'string "' in title_match:
                    title = title_match.split('string "')[1].split('"')[0]
                    track["name"] = title

            # Extract artist (xesam:artist) - it's an array
            if 'xesam:artist' in output:
                artist_section = output.split('xesam:artist')[1]
                artists = []
                for part in artist_section.split('string "')[1:]:
                    if '"' in part:
                        artist = part.split('"')[0]
                        if artist and not artist.startswith('xesam:'):
                            artists.append(artist)
                        else:
                            break
                if artists:
                    track["artists"] = artists

            # Extract album (xesam:album)
            if 'xesam:album' in output:
                album_match = output.split('xesam:album')[1]
                if 'string "' in album_match:
                    album = album_match.split('string "')[1].split('"')[0]
                    track["album"] = album

            # Extract art URL (mpris:artUrl)
            if 'mpris:artUrl' in output:
                art_match = output.split('mpris:artUrl')[1]
                if 'string "' in art_match:
                    art_url = art_match.split('string "')[1].split('"')[0]
                    track["cover_url"] = art_url

            # Extract duration (mpris:length) - in microseconds
            if 'mpris:length' in output:
                length_match = output.split('mpris:length')[1]
                if 'int64 ' in length_match or 'uint64 ' in length_match:
                    try:
                        length_str = length_match.split('int64 ')[1].split()[0] if 'int64 ' in length_match else length_match.split('uint64 ')[1].split()[0]
                        length_us = int(length_str)
                        track["duration_ms"] = length_us // 1000
                    except (ValueError, IndexError):
                        pass

            self._now_playing["track"] = track
            decky.logger.info(f"Parsed metadata: {track}")

            # Emit updated state
            decky.logger.info("Emitting now_playing event to frontend")
            await decky.emit("now_playing", self._now_playing)
            decky.logger.info("Metadata update complete")
            return True

        except Exception as e:
            decky.logger.error(f"Failed to update track metadata: {e}", exc_info=True)
            return False

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

    async def start_spotifyd(self):
        """Start spotifyd service"""
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

    async def stop_spotifyd(self):
        """Stop the spotifyd service"""
        try:
            decky.logger.info("Stopping spotifyd service...")
            success, _, _ = await self._run_systemctl("stop", SERVICE_NAME)

            if success:
                decky.logger.info("Spotifyd service stopped successfully")
            return success

        except Exception as e:
            decky.logger.error(f"Error stopping spotifyd: {e}", exc_info=True)
            return False

    async def enable_spotifyd(self):
        """Enable spotifyd service to start on boot"""
        try:
            decky.logger.info("Enabling spotifyd service for auto-start...")
            success, _, _ = await self._run_systemctl("enable", SERVICE_NAME)

            if success:
                decky.logger.info("Spotifyd service enabled successfully")
            return success

        except Exception as e:
            decky.logger.error(f"Error enabling spotifyd: {e}", exc_info=True)
            return False

    async def disable_spotifyd(self):
        """Disable spotifyd service from starting on boot"""
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
        """Get the status of spotifyd service - callable from frontend"""
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

    async def restart_spotifyd(self):
        """Restart spotifyd service - callable from frontend"""
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

    async def get_settings(self):
        """Get all settings with defaults - callable from frontend"""
        return {
            "speaker_name": settings.getSetting("speaker_name", DEFAULT_SETTINGS["speaker_name"]),
            "bitrate": settings.getSetting("bitrate", DEFAULT_SETTINGS["bitrate"]),
            "device_type": settings.getSetting("device_type", DEFAULT_SETTINGS["device_type"]),
            "initial_volume": settings.getSetting("initial_volume", DEFAULT_SETTINGS["initial_volume"])
        }

    async def save_settings(self, speaker_name: str, bitrate: int, device_type: str, initial_volume: int):
        """Save settings and restart service if running - callable from frontend"""
        try:
            settings.setSetting("speaker_name", speaker_name)
            settings.setSetting("bitrate", bitrate)
            settings.setSetting("device_type", device_type)
            settings.setSetting("initial_volume", initial_volume)
            settings.commit()

            decky.logger.info(f"Settings saved: name={speaker_name}, bitrate={bitrate}, device_type={device_type}, volume={initial_volume}")

            # Regenerate config file with new settings
            self._create_config_file()

            # Restart if running
            status = await self.get_status()
            if status["running"]:
                await self.restart_spotifyd()

            return True
        except Exception as e:
            decky.logger.error(f"Failed to save settings: {e}", exc_info=True)
            return False

    async def _run_dbus_send(self, method: str):
        """Run a dbus-send command to call MPRIS methods on private session bus"""
        try:
            # Find the actual bus name (includes instance ID)
            bus_name = await self._get_mpris_bus_name()
            if not bus_name:
                decky.logger.error("Could not find MPRIS bus name for control")
                return False

            cmd = [
                "dbus-send",
                "--print-reply",
                f"--dest={bus_name}",
                MPRIS_OBJECT_PATH,
                f"{MPRIS_PLAYER_INTERFACE}.{method}"
            ]
            decky.logger.info(f"Running: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_mpris_env()
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                decky.logger.error(f"dbus-send failed: {stderr.decode()}")
                return False

            return True
        except Exception as e:
            decky.logger.error(f"Failed to run dbus-send: {e}", exc_info=True)
            return False

    async def play_pause(self):
        """Toggle play/pause via MPRIS - callable from frontend"""
        success = await self._run_dbus_send("PlayPause")
        if success:
            decky.logger.info("Play/pause toggled")
        return success

    async def next_track(self):
        """Skip to next track via MPRIS - callable from frontend"""
        success = await self._run_dbus_send("Next")
        if success:
            decky.logger.info("Skipped to next track")
        return success

    async def previous_track(self):
        """Skip to previous track via MPRIS - callable from frontend"""
        success = await self._run_dbus_send("Previous")
        if success:
            decky.logger.info("Skipped to previous track")
        return success

    async def get_volume(self):
        """Get current volume from MPRIS (0.0 to 1.0) - callable from frontend"""
        try:
            bus_name = await self._get_mpris_bus_name()
            if not bus_name:
                return self._now_playing.get("volume", 0.5)

            cmd = [
                "dbus-send",
                "--print-reply",
                f"--dest={bus_name}",
                MPRIS_OBJECT_PATH,
                "org.freedesktop.DBus.Properties.Get",
                f"string:{MPRIS_PLAYER_INTERFACE}",
                "string:Volume"
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_mpris_env()
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                decky.logger.error(f"Failed to get volume: {stderr.decode()}")
                return self._now_playing.get("volume", 0.5)

            # Parse volume from dbus-send output
            output = stdout.decode()
            if "double" in output:
                # Extract double value from output like: variant double 0.5
                for line in output.split('\n'):
                    if 'double' in line:
                        volume = float(line.split('double')[-1].strip())
                        self._now_playing["volume"] = volume
                        return volume

            return self._now_playing.get("volume", 0.5)

        except Exception as e:
            decky.logger.error(f"Failed to get volume: {e}")
            return self._now_playing.get("volume", 0.5)

    async def set_volume(self, volume: float):
        """Set volume via MPRIS (0.0 to 1.0) - callable from frontend"""
        try:
            # Clamp volume to valid range
            volume = max(0.0, min(1.0, float(volume)))

            bus_name = await self._get_mpris_bus_name()
            if not bus_name:
                decky.logger.error("Could not find MPRIS bus name for volume control")
                return False

            cmd = [
                "dbus-send",
                "--print-reply",
                f"--dest={bus_name}",
                MPRIS_OBJECT_PATH,
                "org.freedesktop.DBus.Properties.Set",
                f"string:{MPRIS_PLAYER_INTERFACE}",
                "string:Volume",
                f"variant:double:{volume}"
            ]

            decky.logger.info(f"Setting volume to {volume}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_mpris_env()
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                decky.logger.error(f"Failed to set volume: {stderr.decode()}")
                return False

            # Update local state
            self._now_playing["volume"] = volume
            await decky.emit("now_playing", self._now_playing)

            return True

        except Exception as e:
            decky.logger.error(f"Failed to set volume: {e}", exc_info=True)
            return False

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        try:
            decky.logger.info("Starting spotifyd plugin")

            # Read settings (ensure fresh load)
            settings.read()

            # Deploy event handler script
            if not self._deploy_event_handler():
                decky.logger.error("Failed to deploy event handler")
                return

            # Start socket server to receive events
            await self._start_socket_server()

            # Create/update spotifyd config file
            if not self._create_config_file():
                decky.logger.error("Failed to create config file")
                return

            # Create D-Bus session config for private bus
            if not self._create_dbus_config_file():
                decky.logger.error("Failed to create D-Bus config")
                return

            # Create wrapper script for spotifyd with private D-Bus
            if not self._create_wrapper_script():
                decky.logger.error("Failed to create wrapper script")
                return

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
                success = await self.start_spotifyd()

                if success:
                    # Wait a moment and check status again
                    await asyncio.sleep(1)
                    status = await self.get_status()
                    decky.logger.info(f"Plugin loaded successfully. Status: {status}")
                else:
                    decky.logger.error("Failed to start spotifyd service")
            else:
                decky.logger.info("Spotifyd service already running")

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
        await self.stop_spotifyd()
        await self.disable_spotifyd()

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

        # Clean up event handler, config files, wrapper script, and sockets
        try:
            for f in [EVENT_HANDLER_DEST, CONFIG_FILE_PATH, DBUS_CONFIG_FILE,
                      WRAPPER_SCRIPT_PATH, DBUS_ADDRESS_FILE, DBUS_SOCKET_PATH, SOCKET_PATH]:
                if f.exists():
                    f.unlink()
                    decky.logger.info(f"Removed: {f}")
        except Exception as e:
            decky.logger.error(f"Error cleaning up files: {e}")

    async def _migration(self):
        decky.logger.info("Migrating")
        # Recreate config file in case format changed
        self._create_config_file()
        # Recreate D-Bus config and wrapper script
        self._create_dbus_config_file()
        self._create_wrapper_script()
        # Recreate service file in case it needs updating
        self._create_service_file()
        # Reload daemon
        await self._reload_daemon()
