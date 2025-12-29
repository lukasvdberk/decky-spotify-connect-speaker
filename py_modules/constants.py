"""
Constants and configuration for the Decky Spotify Connect Speaker plugin.
"""
import os
import pwd
from pathlib import Path

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
EVENT_HANDLER_SRC = Path(__file__).parent.parent / "defaults" / "event_handler.py"
EVENT_HANDLER_DEST = DATA_DIR / "event_handler.py"
CONFIG_FILE_PATH = DATA_DIR / "spotifyd.conf"

# Private D-Bus session for MPRIS (no system file modifications needed)
DBUS_CONFIG_FILE = DATA_DIR / "dbus-session.conf"
DBUS_SOCKET_PATH = DATA_DIR / "dbus.sock"
DBUS_ADDRESS_FILE = DATA_DIR / "dbus-address"
WRAPPER_SCRIPT_PATH = DATA_DIR / "spotifyd_wrapper.sh"

# Default settings
DEFAULT_SETTINGS = {
    "speaker_name": "decky-spotify",
    "bitrate": 320,
    "device_type": "game-console",
    "initial_volume": 80
}
