import { FC } from "react";
import type { PlaybackState } from "../types";
import { STRINGS, COLORS } from "../constants";
import { formatTime, calculateProgress } from "../utils";

interface ProgressBarProps {
  playbackState: PlaybackState;
  positionMs: number;
  durationMs: number;
}

export const ProgressBar: FC<ProgressBarProps> = ({
  playbackState,
  positionMs,
  durationMs
}) => {
  const progress = calculateProgress(positionMs, durationMs);
  const isPlaying = playbackState === "playing";

  return (
    <div style={{ boxSizing: "border-box", width: "100%", paddingRight: "16px" }}>
      {/* Playback state indicator */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "6px"
      }}>
        <span style={{
          color: isPlaying ? COLORS.SPOTIFY_GREEN : COLORS.TEXT_MUTED,
          fontSize: "12px",
          fontWeight: "bold"
        }}>
          {isPlaying ? `▶ ${STRINGS.STATUS_PLAYING}` : `⏸ ${STRINGS.STATUS_PAUSED}`}
        </span>
      </div>

      {/* Progress bar */}
      <div style={{
        height: "4px",
        backgroundColor: COLORS.BACKGROUND_DARK,
        borderRadius: "2px",
        overflow: "hidden"
      }}>
        <div style={{
          width: `${progress}%`,
          height: "100%",
          backgroundColor: COLORS.SPOTIFY_GREEN,
          borderRadius: "2px",
          transition: "width 0.3s ease"
        }} />
      </div>

      {/* Time display */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        marginTop: "6px",
        fontSize: "11px",
        color: COLORS.TEXT_MUTED
      }}>
        <span>{formatTime(positionMs)}</span>
        <span>{formatTime(durationMs)}</span>
      </div>
    </div>
  );
};
