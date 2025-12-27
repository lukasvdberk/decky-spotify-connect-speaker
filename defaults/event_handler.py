#!/usr/bin/env python3
"""
Event handler script for librespot.
Called by librespot via --onevent flag on playback events.
Sends event data to the Decky plugin via Unix socket.
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

    if event in ("session_connected", "session_disconnected"):
        data["user_name"] = os.environ.get("USER_NAME", "")
        data["connection_id"] = os.environ.get("CONNECTION_ID", "")

    elif event == "track_changed":
        data["name"] = os.environ.get("NAME", "")
        data["artists"] = os.environ.get("ARTISTS", "").split("\n")
        data["album"] = os.environ.get("ALBUM", "")
        covers = os.environ.get("COVERS", "").split("\n")
        data["cover_url"] = covers[0] if covers else ""
        try:
            data["duration_ms"] = int(os.environ.get("DURATION_MS", 0))
        except ValueError:
            data["duration_ms"] = 0

    elif event in ("playing", "paused", "stopped"):
        try:
            data["position_ms"] = int(os.environ.get("POSITION_MS", 0))
        except ValueError:
            data["position_ms"] = 0

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
