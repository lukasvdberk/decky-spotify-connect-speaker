import { FC } from "react";
import { DialogButton, Focusable } from "@decky/ui";
import { FaPlay, FaPause, FaStepBackward, FaStepForward } from "react-icons/fa";
import type { PlaybackState } from "../types";
import { COLORS } from "../constants";

interface PlaybackControlsProps {
  playbackState: PlaybackState;
  isDisabled: boolean;
  onPlayPause: () => void;
  onPrevious: () => void;
  onNext: () => void;
}

const BUTTON_STYLES = {
  small: {
    width: "40px",
    height: "40px",
    minWidth: "40px",
    padding: "0",
    display: "flex" as const,
    alignItems: "center" as const,
    justifyContent: "center" as const,
    borderRadius: "50%"
  },
  large: {
    width: "56px",
    height: "56px",
    minWidth: "56px",
    padding: "0",
    display: "flex" as const,
    alignItems: "center" as const,
    justifyContent: "center" as const,
    background: COLORS.SPOTIFY_GREEN,
    borderRadius: "50%"
  }
};

export const PlaybackControls: FC<PlaybackControlsProps> = ({
  playbackState,
  isDisabled,
  onPlayPause,
  onPrevious,
  onNext
}) => {
  const isPlaying = playbackState === "playing";

  return (
    <Focusable
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        gap: "16px",
        padding: "8px 0",
        width: "100%"
      }}
      flow-children="horizontal"
    >
      <DialogButton
        style={BUTTON_STYLES.small}
        onClick={onPrevious}
        disabled={isDisabled}
      >
        <FaStepBackward />
      </DialogButton>

      <DialogButton
        style={BUTTON_STYLES.large}
        onClick={onPlayPause}
        disabled={isDisabled}
      >
        {isPlaying ? <FaPause /> : <FaPlay style={{ marginLeft: "2px" }} />}
      </DialogButton>

      <DialogButton
        style={BUTTON_STYLES.small}
        onClick={onNext}
        disabled={isDisabled}
      >
        <FaStepForward />
      </DialogButton>
    </Focusable>
  );
};
