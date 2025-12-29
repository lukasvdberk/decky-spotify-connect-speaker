"""
Event handling via Unix socket for spotifyd events.
"""
import os
import json
import asyncio
import decky

from constants import DATA_DIR, SOCKET_PATH


class EventHandler:
    """Handles spotifyd events via Unix socket server."""

    def __init__(self):
        self._server = None
        self._event_callback = None

    def set_event_callback(self, callback):
        """
        Register a callback function for events.

        Args:
            callback: Async function that receives event dict
        """
        self._event_callback = callback

    async def start_server(self):
        """Start Unix socket server to receive events from event_handler.py."""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)

            # Remove existing socket if present
            if SOCKET_PATH.exists():
                SOCKET_PATH.unlink()

            server = await asyncio.start_unix_server(
                self._handle_connection,
                path=str(SOCKET_PATH)
            )
            # Allow event handler (running as user) to connect
            os.chmod(SOCKET_PATH, 0o666)
            self._server = server
            decky.logger.info(f"Socket server started at {SOCKET_PATH}")

        except Exception as e:
            decky.logger.error(f"Failed to start socket server: {e}", exc_info=True)

    async def stop_server(self):
        """Stop the Unix socket server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
            decky.logger.info("Socket server stopped")

        # Clean up socket file
        if SOCKET_PATH.exists():
            try:
                SOCKET_PATH.unlink()
            except Exception:
                pass

    async def _handle_connection(self, reader, writer):
        """Handle incoming event from event_handler.py."""
        try:
            data = await reader.read(4096)
            writer.close()
            await writer.wait_closed()

            if data:
                event = json.loads(data.decode())
                if self._event_callback:
                    await self._event_callback(event)
                else:
                    decky.logger.warning("Received event but no callback registered")
        except Exception as e:
            decky.logger.error(f"Error handling event connection: {e}")

    @property
    def is_running(self):
        """Check if the socket server is running."""
        return self._server is not None
