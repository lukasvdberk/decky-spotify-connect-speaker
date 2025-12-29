/**
 * Format milliseconds to mm:ss display format
 */
export const formatTime = (ms: number): string => {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

/**
 * Calculate progress percentage for playback bar
 */
export const calculateProgress = (positionMs: number, durationMs: number): number => {
  if (durationMs <= 0) return 0;
  return (positionMs / durationMs) * 100;
};

/**
 * Normalize volume from percentage (0-100) to decimal (0.0-1.0)
 */
export const normalizeVolume = (percentage: number): number => {
  return percentage / 100.0;
};

/**
 * Denormalize volume from decimal (0.0-1.0) to percentage (0-100)
 */
export const denormalizeVolume = (decimal: number): number => {
  return Math.round(decimal * 100);
};
