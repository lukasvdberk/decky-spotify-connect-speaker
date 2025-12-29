"""
Configuration file generation for spotifyd, D-Bus, and systemd service.
"""
import os
import shutil
import decky

from constants import (
    DATA_DIR, CONFIG_FILE_PATH, EVENT_HANDLER_SRC, EVENT_HANDLER_DEST,
    DBUS_CONFIG_FILE, DBUS_SOCKET_PATH, WRAPPER_SCRIPT_PATH,
    SPOTIFYD_BIN, SYSTEMD_USER_DIR, SERVICE_NAME, DEFAULT_SETTINGS
)


class ConfigManager:
    """Manages configuration file generation for spotifyd and related services."""

    def __init__(self, settings):
        """
        Initialize ConfigManager with settings.

        Args:
            settings: SettingsManager instance for reading plugin settings
        """
        self._settings = settings

    def _get_setting(self, key):
        """Get a setting value with fallback to default."""
        return self._settings.getSetting(key, DEFAULT_SETTINGS.get(key))

    def get_config_content(self):
        """Generate spotifyd config file content with current settings."""
        speaker_name = self._get_setting("speaker_name")
        bitrate = self._get_setting("bitrate")
        device_type = self._get_setting("device_type")
        initial_volume = self._get_setting("initial_volume")

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

    def create_config_file(self):
        """Create spotifyd config file."""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE_PATH, 'w') as f:
                f.write(self.get_config_content())
            decky.logger.info(f"Created config file at {CONFIG_FILE_PATH}")
            return True
        except Exception as e:
            decky.logger.error(f"Failed to create config file: {e}", exc_info=True)
            return False

    def get_dbus_config_content(self):
        """Generate D-Bus session config for private bus."""
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

    def create_dbus_config_file(self):
        """Create D-Bus session config file."""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(DBUS_CONFIG_FILE, 'w') as f:
                f.write(self.get_dbus_config_content())
            decky.logger.info(f"Created D-Bus config at {DBUS_CONFIG_FILE}")
            return True
        except Exception as e:
            decky.logger.error(f"Failed to create D-Bus config: {e}", exc_info=True)
            return False

    def get_wrapper_script_content(self):
        """Generate wrapper script that starts private D-Bus and spotifyd."""
        return f"""#!/bin/bash
# Wrapper script to run spotifyd with its own private D-Bus session

# Clean up any existing socket
rm -f "{DBUS_SOCKET_PATH}"

# Start private D-Bus daemon
dbus-daemon --config-file="{DBUS_CONFIG_FILE}" --fork --print-address > "{DATA_DIR / 'dbus-address'}"

# Wait for socket to be created and set permissions so root (Decky plugin) can access it
sleep 0.5
chmod 666 "{DBUS_SOCKET_PATH}"

# Read the bus address
export DBUS_SESSION_BUS_ADDRESS=$(cat "{DATA_DIR / 'dbus-address'}")

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

    def create_wrapper_script(self):
        """Create wrapper script for spotifyd with private D-Bus."""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(WRAPPER_SCRIPT_PATH, 'w') as f:
                f.write(self.get_wrapper_script_content())
            os.chmod(WRAPPER_SCRIPT_PATH, 0o755)
            decky.logger.info(f"Created wrapper script at {WRAPPER_SCRIPT_PATH}")
            return True
        except Exception as e:
            decky.logger.error(f"Failed to create wrapper script: {e}", exc_info=True)
            return False

    def get_service_content(self):
        """Generate systemd service file content."""
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

    def create_service_file(self):
        """Create systemd service file."""
        try:
            SYSTEMD_USER_DIR.mkdir(parents=True, exist_ok=True)
            service_path = SYSTEMD_USER_DIR / SERVICE_NAME
            with open(service_path, 'w') as f:
                f.write(self.get_service_content())
            decky.logger.info(f"Created service file at {service_path}")
            return True
        except Exception as e:
            decky.logger.error(f"Failed to create service file: {e}", exc_info=True)
            return False

    def deploy_event_handler(self):
        """Copy event_handler.py to user data directory."""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy(EVENT_HANDLER_SRC, EVENT_HANDLER_DEST)
            os.chmod(EVENT_HANDLER_DEST, 0o755)
            decky.logger.info(f"Deployed event handler to {EVENT_HANDLER_DEST}")
            return True
        except Exception as e:
            decky.logger.error(f"Failed to deploy event handler: {e}", exc_info=True)
            return False

    def create_all(self):
        """Create all configuration files. Returns True if all succeeded."""
        success = True
        if not self.deploy_event_handler():
            success = False
        if not self.create_config_file():
            success = False
        if not self.create_dbus_config_file():
            success = False
        if not self.create_wrapper_script():
            success = False
        if not self.create_service_file():
            success = False
        return success
