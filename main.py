import os
import subprocess

# The decky plugin module is located at decky-loader/plugin
# For easy intellisense checkout the decky-loader code repo
# and add the `decky-loader/plugin/imports` path to `python.analysis.extraPaths` in `.vscode/settings.json`
import decky
import asyncio

# TODO move to a the configurable settings manager mentioned in the docs
LIBRESPOT_BIN = "/home/deck/librespot"
LIBRESPOT_SPEAKER_NAME="decky"
class Plugin:
    async def long_running(self):
        # Passing through a bunch of random data, just as an example
        await decky.emit("timer_event", "Hello from the backend!", True, 2)

        decky.logger.info("Attempting to start librespot")
        # start speaker in background
        subprocess.Popen([LIBRESPOT_BIN, "-n", LIBRESPOT_SPEAKER_NAME, "-b", "320"]) 

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        self.loop = asyncio.get_event_loop()
        decky.logger.info("Starting librespot plugin")

    # Function called first during the unload process, utilize this to handle your plugin being stopped, but not
    # completely removed
    async def _unload(self):
        decky.logger.info("Goodnight World!")

        # TODO add the stopping of librespot
        pass

    # Function called after `_unload` during uninstall, utilize this to clean up processes and other remnants of your
    # plugin that may remain on the system
    async def _uninstall(self):
        decky.logger.info("Goodbye World!")
        pass

    async def _migration(self):
        pass