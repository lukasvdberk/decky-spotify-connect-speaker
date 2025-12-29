// Service status from backend
export interface ServiceStatus {
  running: boolean;
  enabled: boolean;
  service: string;
  state: string;
}

// Track information
export interface TrackInfo {
  name: string;
  artists: string[];
  album: string;
  cover_url: string;
  duration_ms: number;
}

// Playback state
export type PlaybackState = "playing" | "paused" | "stopped";

// Now playing state from backend
export interface NowPlayingState {
  connected: boolean;
  user_name: string | null;
  connection_id: string | null;
  track: TrackInfo | null;
  playback_state: PlaybackState;
  position_ms: number;
  volume: number; // 0.0 to 1.0
}

// Settings from backend
export interface Settings {
  speaker_name: string;
  bitrate: number;
  device_type: string;
  initial_volume: number;
}

// Dropdown option type (matches @decky/ui expectations)
export interface DropdownOption<T> {
  data: T;
  label: string;
}
