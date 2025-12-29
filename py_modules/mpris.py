"""
MPRIS D-Bus interface for playback control and metadata.
"""
import os
import asyncio
import decky

from constants import (
    DECKY_USER_UID, DBUS_ADDRESS_FILE,
    MPRIS_BUS_NAME_PREFIX, MPRIS_OBJECT_PATH, MPRIS_PLAYER_INTERFACE
)


class MPRISController:
    """Controls spotifyd playback via MPRIS D-Bus interface."""

    def _get_user_env(self):
        """Get environment for running user commands outside Decky sandbox."""
        env = os.environ.copy()

        # Clear LD_LIBRARY_PATH to avoid Decky's sandboxed libraries
        env.pop("LD_LIBRARY_PATH", None)
        env.pop("LD_PRELOAD", None)

        # Set user session variables
        if "XDG_RUNTIME_DIR" not in env:
            env["XDG_RUNTIME_DIR"] = f"/run/user/{DECKY_USER_UID}"
        if "DBUS_SESSION_BUS_ADDRESS" not in env:
            env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path=/run/user/{DECKY_USER_UID}/bus"

        return env

    def _get_mpris_env(self):
        """Get environment for MPRIS dbus-send using private bus address."""
        env = self._get_user_env()

        # Read the bus address from the file written by the wrapper script
        try:
            if DBUS_ADDRESS_FILE.exists():
                bus_address = DBUS_ADDRESS_FILE.read_text().strip()
                if bus_address:
                    env["DBUS_SESSION_BUS_ADDRESS"] = bus_address
                else:
                    decky.logger.warning("Bus address file exists but is empty")
            else:
                decky.logger.warning(f"Bus address file does not exist: {DBUS_ADDRESS_FILE}")
        except Exception as e:
            decky.logger.warning(f"Failed to read MPRIS bus address: {e}")

        return env

    async def get_bus_name(self):
        """Find the actual MPRIS bus name (includes instance ID)."""
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

    async def _run_dbus_send(self, method):
        """Run a dbus-send command to call MPRIS methods on private session bus."""
        try:
            # Find the actual bus name (includes instance ID)
            bus_name = await self.get_bus_name()
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
        """Toggle play/pause via MPRIS."""
        success = await self._run_dbus_send("PlayPause")
        if success:
            decky.logger.info("Play/pause toggled")
        return success

    async def next_track(self):
        """Skip to next track via MPRIS."""
        success = await self._run_dbus_send("Next")
        if success:
            decky.logger.info("Skipped to next track")
        return success

    async def previous_track(self):
        """Skip to previous track via MPRIS."""
        success = await self._run_dbus_send("Previous")
        if success:
            decky.logger.info("Skipped to previous track")
        return success

    async def get_volume(self, default=0.5):
        """Get current volume from MPRIS (0.0 to 1.0)."""
        try:
            bus_name = await self.get_bus_name()
            if not bus_name:
                return default

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
                return default

            # Parse volume from dbus-send output
            output = stdout.decode()
            if "double" in output:
                # Extract double value from output like: variant double 0.5
                for line in output.split('\n'):
                    if 'double' in line:
                        volume = float(line.split('double')[-1].strip())
                        return volume

            return default

        except Exception as e:
            decky.logger.error(f"Failed to get volume: {e}")
            return default

    async def set_volume(self, volume):
        """Set volume via MPRIS (0.0 to 1.0). Returns True on success."""
        try:
            # Clamp volume to valid range
            volume = max(0.0, min(1.0, float(volume)))

            bus_name = await self.get_bus_name()
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

            return True

        except Exception as e:
            decky.logger.error(f"Failed to set volume: {e}", exc_info=True)
            return False

    async def get_metadata(self):
        """Fetch track metadata from MPRIS. Returns dict or None on failure."""
        try:
            bus_name = await self.get_bus_name()
            if not bus_name:
                decky.logger.error("Could not find MPRIS bus name")
                return None

            decky.logger.info(f"Fetching metadata from {bus_name}")

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
                return None

            # Parse dbus-send output for metadata
            output = stdout.decode()
            track = {}

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

            decky.logger.info(f"Parsed metadata: {track}")
            return track

        except Exception as e:
            decky.logger.error(f"Failed to get track metadata: {e}", exc_info=True)
            return None
