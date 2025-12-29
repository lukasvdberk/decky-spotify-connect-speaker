import type { DropdownOption } from "./types";

// Bitrate options for dropdown
export const BITRATE_OPTIONS: DropdownOption<number>[] = [
  { data: 96, label: "96 kbps (Low)" },
  { data: 160, label: "160 kbps (Normal)" },
  { data: 320, label: "320 kbps (High)" }
];

// Device type options for dropdown (must match spotifyd --device-type values)
export const DEVICE_TYPE_OPTIONS: DropdownOption<string>[] = [
  { data: "computer", label: "Computer" },
  { data: "tablet", label: "Tablet" },
  { data: "smartphone", label: "Smartphone" },
  { data: "speaker", label: "Speaker" },
  { data: "tv", label: "TV" },
  { data: "avr", label: "AVR (Audio/Video Receiver)" },
  { data: "stb", label: "STB (Set-Top Box)" },
  { data: "audio_dongle", label: "Audio Dongle" },
  { data: "game_console", label: "Game Console" },
  { data: "cast_audio", label: "Cast Audio" },
  { data: "cast_video", label: "Cast Video" },
  { data: "automobile", label: "Automobile" },
  { data: "smartwatch", label: "Smartwatch" },
  { data: "chromebook", label: "Chromebook" },
  { data: "car_thing", label: "Car Thing" },
  { data: "observer", label: "Observer" }
];

// UI Strings
export const STRINGS = {
  // Plugin metadata
  PLUGIN_NAME: "Spotify Connect Speaker",
  PLUGIN_TITLE: "Spotify Connect",

  // Section titles
  SECTION_NOW_PLAYING: "Now Playing",
  SECTION_SERVICE_CONTROLS: "Service Controls",
  SECTION_SPEAKER_SETTINGS: "Speaker Settings",

  // Field labels
  LABEL_STATUS: "Status",
  LABEL_SPEAKER_NAME: "Speaker Name",
  LABEL_BITRATE: "Bitrate",
  LABEL_DEVICE_TYPE: "Device Type",
  LABEL_VOLUME: "Volume",
  LABEL_AUTOSTART: "Auto-start on boot",

  // Status messages
  STATUS_RUNNING: "Running",
  STATUS_STOPPED: "Stopped",
  STATUS_UNKNOWN: "unknown",
  STATUS_PLAYING: "Playing",
  STATUS_PAUSED: "Paused",

  // Button labels
  BTN_START_SERVICE: "Start Service",
  BTN_STOP_SERVICE: "Stop Service",
  BTN_RESTART_SERVICE: "Restart Service",
  BTN_SAVE_SETTINGS: "Save Settings",
  BTN_SETTINGS: "Settings",

  // Loading states
  LOADING_STARTING: "Starting...",
  LOADING_STOPPING: "Stopping...",
  LOADING_RESTARTING: "Restarting...",
  LOADING_SAVING: "Saving...",

  // Now playing states
  NP_SERVICE_NOT_RUNNING: "Service not running",
  NP_WAITING_CONNECTION: "Waiting for connection...",
  NP_CONNECTED_NO_TRACK: "Connected - No track playing",
  NP_UNKNOWN_ARTIST: "Unknown Artist",
  NP_UNKNOWN_ALBUM: "Unknown Album",

  // Connection guide
  GUIDE_STEP_1: "1. Open Spotify on your phone or computer",
  GUIDE_STEP_2: "2. Play any song",
  GUIDE_STEP_3: "3. Tap the \"Devices\" icon",
  GUIDE_STEP_4: "4. Select \"decky-spotify\"",

  // Toast messages - success
  TOAST_SUCCESS: "Success",
  TOAST_STARTED: "Spotify speaker started",
  TOAST_STOPPED: "Spotify speaker stopped",
  TOAST_RESTARTED: "Spotify speaker restarted",
  TOAST_SETTINGS_SAVED: "Settings saved",
  TOAST_SETTINGS_SAVED_RESTARTED: "Service restarted with new settings",
  TOAST_SETTINGS_SAVED_SUCCESS: "Settings saved successfully",
  TOAST_AUTOSTART_ENABLED: "Auto-start enabled",
  TOAST_AUTOSTART_DISABLED: "Auto-start disabled",

  // Toast messages - error
  TOAST_ERROR: "Error",
  TOAST_FAILED_START: "Failed to start service",
  TOAST_FAILED_STOP: "Failed to stop service",
  TOAST_FAILED_RESTART: "Failed to restart service",
  TOAST_FAILED_SAVE: "Failed to save settings",
  TOAST_FAILED_STATUS: "Failed to get service status",
  TOAST_FAILED_LOAD_SETTINGS: "Failed to load settings",
  TOAST_OPERATION_FAILED: "Operation failed",
  TOAST_FAILED_AUTOSTART_ENABLE: "Failed to enable auto-start",
  TOAST_FAILED_AUTOSTART_DISABLE: "Failed to disable auto-start"
} as const;

// Routes
export const ROUTES = {
  SETTINGS: "/decky-spotify-settings"
} as const;

// Colors
export const COLORS = {
  SPOTIFY_GREEN: "#1DB954",
  TEXT_PRIMARY: "#fff",
  TEXT_SECONDARY: "#b8bcbf",
  TEXT_MUTED: "#888",
  TEXT_VERY_MUTED: "#8b929a",
  BACKGROUND_DARK: "#23262e",
  STATUS_STOPPED: "#888888"
} as const;

// Timing constants
export const TIMING = {
  VOLUME_DEBOUNCE_MS: 1500,
  POSITION_UPDATE_INTERVAL_MS: 1000
} as const;
