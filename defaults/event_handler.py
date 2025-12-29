#!/usr/bin/env python3
"""
Event handler script for spotifyd.
Called by spotifyd via --onevent flag on playback events.
Sends event data to the Decky plugin via Unix socket.

Spotifyd events (from logs):
- sessionconnected: User connected to Spotify
- clientchanged: Client changed
- volumeset: Volume changed
- autoplay_changed, filterexplicit_changed, shuffle_changed, repeat_changed: Settings changed
- playrequestid_changed: Play request changed
- load: Track loading
- change: Track changed
- start: Playback started/resumed
- pause: Playback paused
- stop: Playback stopped
- seeked: Position changed
- endoftrack: Track finished playing

Environment variables provided by spotifyd:
- PLAYER_EVENT: Event type
- TRACK_ID: Spotify track ID
- DURATION_MS: Track duration in milliseconds
- POSITION_MS: Current position in milliseconds
- OLD_TRACK_ID: Previous track ID (for change events)
"""
import os
import json
import socket

SOCKET_PATH = os.path.expanduser("~/.local/share/decky-spotify/event.sock")


def main():
    event = os.environ.get("PLAYER_EVENT")
    if not event:
        return

    data = {"event": event}

    # Always include track_id if available
    track_id = os.environ.get("TRACK_ID", "")
    if track_id:
        data["track_id"] = track_id

    # Track change event
    if event == "change":
        data["old_track_id"] = os.environ.get("OLD_TRACK_ID", "")
        try:
            data["duration_ms"] = int(os.environ.get("DURATION_MS", 0))
        except ValueError:
            data["duration_ms"] = 0

    # Playback state events - spotifyd uses "start" for play
    elif event in ("start", "pause", "stop", "endoftrack", "seeked"):
        try:
            data["position_ms"] = int(os.environ.get("POSITION_MS", 0))
        except ValueError:
            data["position_ms"] = 0
        try:
            data["duration_ms"] = int(os.environ.get("DURATION_MS", 0))
        except ValueError:
            data["duration_ms"] = 0

    # Send to socket
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(1.0)  # Don't block forever
        sock.connect(SOCKET_PATH)
        sock.sendall(json.dumps(data).encode())
        sock.close()
    except Exception:
        pass  # Socket might not be ready, silently fail


if __name__ == "__main__":
    main()
