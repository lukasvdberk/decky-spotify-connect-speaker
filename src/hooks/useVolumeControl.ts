import { useState, useEffect, useRef, useCallback } from "react";
import { TIMING } from "../constants";
import { normalizeVolume, denormalizeVolume } from "../utils";
import * as api from "../api";

interface UseVolumeControlReturn {
  localVolume: number;
  isAdjustingVolume: boolean;
  handleVolumeChange: (value: number) => void;
}

export const useVolumeControl = (backendVolume: number | undefined): UseVolumeControlReturn => {
  const [localVolume, setLocalVolume] = useState(50);
  const [isAdjustingVolume, setIsAdjustingVolume] = useState(false);
  const volumeTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Sync local volume with backend when not adjusting
  useEffect(() => {
    if (!isAdjustingVolume && backendVolume !== undefined) {
      setLocalVolume(denormalizeVolume(backendVolume));
    }
  }, [backendVolume, isAdjustingVolume]);

  const handleVolumeChange = useCallback((value: number) => {
    setLocalVolume(value);
    setIsAdjustingVolume(true);

    // Clear existing timeout
    if (volumeTimeoutRef.current) {
      clearTimeout(volumeTimeoutRef.current);
    }

    // Send volume to backend
    api.setVolume(normalizeVolume(value)).catch((error) => {
      console.error("Volume change error:", error);
    });

    // Reset adjusting state after delay
    volumeTimeoutRef.current = setTimeout(() => {
      setIsAdjustingVolume(false);
    }, TIMING.VOLUME_DEBOUNCE_MS);
  }, []);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (volumeTimeoutRef.current) {
        clearTimeout(volumeTimeoutRef.current);
      }
    };
  }, []);

  return {
    localVolume,
    isAdjustingVolume,
    handleVolumeChange
  };
};
