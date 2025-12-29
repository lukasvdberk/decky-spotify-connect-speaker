"""
Decky Loader plugin for Spotify Connect Speaker using spotifyd.
"""
import asyncio
import decky
from settings import SettingsManager

# Import from py_modules
from constants import (
    SETTINGS_DIR, DEFAULT_SETTINGS, SYSTEMD_USER_DIR, SERVICE_NAME,
    EVENT_HANDLER_DEST, CONFIG_FILE_PATH, DBUS_CONFIG_FILE,
    WRAPPER_SCRIPT_PATH, DBUS_ADDRESS_FILE, DBUS_SOCKET_PATH, SOCKET_PATH
)
from config import ConfigManager
from service import ServiceManager
from mpris import MPRISController
from events import EventHandler

# Settings manager initialization
settings = SettingsManager(name="settings", settings_directory=SETTINGS_DIR)
settings.read()


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
        # Initialize module managers
        self.config = ConfigManager(settings)
        self.service = ServiceManager()
        self.mpris = MPRISController()
        self.events = EventHandler()

    # -------------------------------------------------------------------------
    # Event Processing (stays in Plugin as it manages local state)
    # -------------------------------------------------------------------------

    async def _on_event(self, event):
        """Process event from spotifyd and update internal state."""
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
        await decky.emit("now_playing", self._now_playing)

    async def _update_volume(self):
        """Fetch current volume from MPRIS and update state."""
        volume = await self.mpris.get_volume(self._now_playing.get("volume", 0.5))
        self._now_playing["volume"] = volume
        await decky.emit("now_playing", self._now_playing)

    async def _update_track_metadata_delayed(self):
        """Fetch track metadata with delay to let MPRIS initialize."""
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
        """Fetch track metadata from MPRIS and update now_playing state."""
        metadata = await self.mpris.get_metadata()
        if metadata is None:
            return False

        # Merge metadata into existing track info
        track = self._now_playing.get("track", {})
        track.update(metadata)
        self._now_playing["track"] = track

        # Emit updated state
        decky.logger.info("Emitting now_playing event to frontend")
        await decky.emit("now_playing", self._now_playing)
        decky.logger.info("Metadata update complete")
        return True

    # -------------------------------------------------------------------------
    # Frontend-callable methods - Service Control
    # -------------------------------------------------------------------------

    async def start_spotifyd(self):
        """Start spotifyd service - callable from frontend."""
        return await self.service.start()

    async def stop_spotifyd(self):
        """Stop the spotifyd service - callable from frontend."""
        return await self.service.stop()

    async def enable_spotifyd(self):
        """Enable spotifyd service to start on boot - callable from frontend."""
        return await self.service.enable()

    async def disable_spotifyd(self):
        """Disable spotifyd service from starting on boot - callable from frontend."""
        return await self.service.disable()

    async def get_status(self):
        """Get the status of spotifyd service - callable from frontend."""
        return await self.service.get_status()

    async def restart_spotifyd(self):
        """Restart spotifyd service - callable from frontend."""
        return await self.service.restart()

    async def get_logs(self, lines=50):
        """Get recent logs from the service - callable from frontend."""
        return await self.service.get_logs(lines)

    # -------------------------------------------------------------------------
    # Frontend-callable methods - Now Playing
    # -------------------------------------------------------------------------

    async def get_now_playing(self):
        """Get current playback state - callable from frontend."""
        return self._now_playing

    # -------------------------------------------------------------------------
    # Frontend-callable methods - Settings
    # -------------------------------------------------------------------------

    async def get_settings(self):
        """Get all settings with defaults - callable from frontend."""
        return {
            "speaker_name": settings.getSetting("speaker_name", DEFAULT_SETTINGS["speaker_name"]),
            "bitrate": settings.getSetting("bitrate", DEFAULT_SETTINGS["bitrate"]),
            "device_type": settings.getSetting("device_type", DEFAULT_SETTINGS["device_type"]),
            "initial_volume": settings.getSetting("initial_volume", DEFAULT_SETTINGS["initial_volume"])
        }

    async def save_settings(self, speaker_name: str, bitrate: int, device_type: str, initial_volume: int):
        """Save settings and restart service if running - callable from frontend."""
        try:
            settings.setSetting("speaker_name", speaker_name)
            settings.setSetting("bitrate", bitrate)
            settings.setSetting("device_type", device_type)
            settings.setSetting("initial_volume", initial_volume)
            settings.commit()

            decky.logger.info(f"Settings saved: name={speaker_name}, bitrate={bitrate}, device_type={device_type}, volume={initial_volume}")

            # Regenerate config file with new settings
            self.config.create_config_file()

            # Restart if running
            status = await self.service.get_status()
            if status["running"]:
                await self.service.restart()

            return True
        except Exception as e:
            decky.logger.error(f"Failed to save settings: {e}", exc_info=True)
            return False

    # -------------------------------------------------------------------------
    # Frontend-callable methods - Playback Control
    # -------------------------------------------------------------------------

    async def play_pause(self):
        """Toggle play/pause via MPRIS - callable from frontend."""
        return await self.mpris.play_pause()

    async def next_track(self):
        """Skip to next track via MPRIS - callable from frontend."""
        return await self.mpris.next_track()

    async def previous_track(self):
        """Skip to previous track via MPRIS - callable from frontend."""
        return await self.mpris.previous_track()

    async def get_volume(self):
        """Get current volume from MPRIS (0.0 to 1.0) - callable from frontend."""
        return await self.mpris.get_volume(self._now_playing.get("volume", 0.5))

    async def set_volume(self, volume: float):
        """Set volume via MPRIS (0.0 to 1.0) - callable from frontend."""
        success = await self.mpris.set_volume(volume)
        if success:
            # Update local state
            self._now_playing["volume"] = max(0.0, min(1.0, float(volume)))
            await decky.emit("now_playing", self._now_playing)
        return success

    # -------------------------------------------------------------------------
    # Lifecycle Methods
    # -------------------------------------------------------------------------

    async def _main(self):
        """Asyncio-compatible long-running code, executed in a task when the plugin is loaded."""
        try:
            decky.logger.info("Starting spotifyd plugin")

            # Read settings (ensure fresh load)
            settings.read()

            # Set up event callback
            self.events.set_event_callback(self._on_event)

            # Start socket server to receive events
            await self.events.start_server()

            # Create all configuration files
            if not self.config.create_all():
                decky.logger.error("Failed to create configuration files")
                return

            # Reload daemon to pick up new/updated service file
            await self.service.reload_daemon()

            # Check current status
            status = await self.service.get_status()
            decky.logger.info(f"Current status: {status}")

            # Start the service if not already running
            if not status["running"]:
                success = await self.service.start()

                if success:
                    # Wait a moment and check status again
                    await asyncio.sleep(1)
                    status = await self.service.get_status()
                    decky.logger.info(f"Plugin loaded successfully. Status: {status}")
                else:
                    decky.logger.error("Failed to start spotifyd service")
            else:
                decky.logger.info("Spotifyd service already running")

        except Exception as e:
            decky.logger.error(f"Error in _main: {e}", exc_info=True)

    async def _unload(self):
        """Function called first during the unload process."""
        decky.logger.info("Unloading plugin")
        # Stop the socket server
        await self.events.stop_server()
        # Don't stop the service on unload - let it keep running
        # Users can manually stop it if they want

    async def _uninstall(self):
        """Function called after `_unload` during uninstall."""
        decky.logger.info("Uninstalling plugin")

        # Stop and disable the service
        await self.service.stop()
        await self.service.disable()

        # Remove service file
        try:
            service_path = SYSTEMD_USER_DIR / SERVICE_NAME
            if service_path.exists():
                service_path.unlink()
                decky.logger.info(f"Removed service file: {service_path}")

            # Reload systemd
            await self.service.reload_daemon()

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
        """Called on plugin update."""
        decky.logger.info("Migrating")
        # Recreate all config files in case format changed
        self.config.create_all()
        # Reload daemon
        await self.service.reload_daemon()
