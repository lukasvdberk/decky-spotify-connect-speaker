import { useState, useCallback } from "react";
import * as api from "../api";

interface UsePlaybackControlsReturn {
  isControlling: boolean;
  handlePlayPause: () => Promise<void>;
  handlePrevious: () => Promise<void>;
  handleNext: () => Promise<void>;
}

export const usePlaybackControls = (): UsePlaybackControlsReturn => {
  const [isControlling, setIsControlling] = useState(false);

  const handlePlayPause = useCallback(async () => {
    setIsControlling(true);
    try {
      await api.playPause();
    } catch (error) {
      console.error("Play/pause error:", error);
    } finally {
      setIsControlling(false);
    }
  }, []);

  const handlePrevious = useCallback(async () => {
    setIsControlling(true);
    try {
      await api.previousTrack();
    } catch (error) {
      console.error("Previous track error:", error);
    } finally {
      setIsControlling(false);
    }
  }, []);

  const handleNext = useCallback(async () => {
    setIsControlling(true);
    try {
      await api.nextTrack();
    } catch (error) {
      console.error("Next track error:", error);
    } finally {
      setIsControlling(false);
    }
  }, []);

  return {
    isControlling,
    handlePlayPause,
    handlePrevious,
    handleNext
  };
};
