import { useState, useEffect } from "react";
import { addEventListener, removeEventListener } from "@decky/api";
import type { NowPlayingState } from "../types";
import { TIMING } from "../constants";
import * as api from "../api";

interface UseNowPlayingReturn {
  nowPlaying: NowPlayingState | null;
  displayPosition: number;
}

export const useNowPlaying = (isServiceRunning: boolean): UseNowPlayingReturn => {
  const [nowPlaying, setNowPlaying] = useState<NowPlayingState | null>(null);
  const [displayPosition, setDisplayPosition] = useState(0);

  // Subscribe to now playing updates when service is running
  useEffect(() => {
    if (!isServiceRunning) {
      setNowPlaying(null);
      return;
    }

    // Fetch initial state
    api.getNowPlaying().then(setNowPlaying).catch(console.error);

    // Listen for real-time updates from backend
    const listener = addEventListener<[NowPlayingState]>(
      "now_playing",
      (state) => setNowPlaying(state)
    );

    return () => removeEventListener("now_playing", listener);
  }, [isServiceRunning]);

  // Sync position when nowPlaying updates
  useEffect(() => {
    if (nowPlaying) {
      setDisplayPosition(nowPlaying.position_ms);
    }
  }, [nowPlaying?.position_ms]);

  // Timer to increment position while playing
  useEffect(() => {
    if (nowPlaying?.playback_state !== "playing" || !nowPlaying?.track) {
      return;
    }

    const interval = setInterval(() => {
      setDisplayPosition((prev) => {
        const newPos = prev + TIMING.POSITION_UPDATE_INTERVAL_MS;
        // Cap at track duration
        const duration = nowPlaying.track?.duration_ms || 0;
        return newPos > duration ? duration : newPos;
      });
    }, TIMING.POSITION_UPDATE_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [nowPlaying?.playback_state, nowPlaying?.track]);

  return { nowPlaying, displayPosition };
};
