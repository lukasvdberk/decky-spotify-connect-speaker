import { callable } from "@decky/api";
import type { ServiceStatus, NowPlayingState, Settings } from "./types";

// Service control
export const getStatus = callable<[], ServiceStatus>("get_status");
export const startSpotifyd = callable<[], boolean>("start_spotifyd");
export const stopSpotifyd = callable<[], boolean>("stop_spotifyd");
export const enableSpotifyd = callable<[], boolean>("enable_spotifyd");
export const disableSpotifyd = callable<[], boolean>("disable_spotifyd");
export const restartSpotifyd = callable<[], boolean>("restart_spotifyd");

// Now playing
export const getNowPlaying = callable<[], NowPlayingState>("get_now_playing");

// Settings
export const getSettings = callable<[], Settings>("get_settings");
export const saveSettings = callable<[string, number, string, number], boolean>("save_settings");

// Playback controls (via MPRIS)
export const playPause = callable<[], boolean>("play_pause");
export const nextTrack = callable<[], boolean>("next_track");
export const previousTrack = callable<[], boolean>("previous_track");
export const setVolume = callable<[number], boolean>("set_volume");
