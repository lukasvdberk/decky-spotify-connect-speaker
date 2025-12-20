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
    librespot_process = None
    async def long_running(self):
        decky.logger.info("Attempting to start librespot")
        await decky.emit("timer_event", "Starting librespot....", True, 2)

        # start speaker in background and capture output
        librespot_process = subprocess.Popen(
            [LIBRESPOT_BIN, "-n", LIBRESPOT_SPEAKER_NAME, "-b", "320"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # TODO maybe emit to frontend eventually?
        # Read and display output in real-time
        # try:
        #     for line in librespot_process.stdout:
        #         print(f"STDOUT: {line.rstrip()}")
        #     for line in librespot_process.stderr:
        #         print(f"STDERR: {line.rstrip()}")
        # except KeyboardInterrupt:
        #     print("Interrupted, shutting down...")
        # finally:
        #     process.terminate()
        #     try:
        #         process.wait(timeout=5)
        #     except subprocess.TimeoutExpired:
        #         process.kill()

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        self.loop = asyncio.get_event_loop()
        decky.logger.info("Starting librespot plugin")

    # Function called first during the unload process, utilize this to handle your plugin being stopped, but not
    # completely removed
    async def _unload(self):
        decky.logger.info("Stopping plugin, trying to kill speaker")

        if librespot is not None:
            librespot_process.terminate()
            try:
                librespot_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                librespot_process.kill()

    # Function called after `_unload` during uninstall, utilize this to clean up processes and other remnants of your
    # plugin that may remain on the system
    async def _uninstall(self):
        decky.logger.info("Goodbye World!")
        pass

    async def _migration(self):
        pass