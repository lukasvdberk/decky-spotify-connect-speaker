import { FC } from "react";
import { PanelSection, PanelSectionRow, Field } from "@decky/ui";
import type { ServiceStatus, NowPlayingState } from "../types";
import { STRINGS, COLORS } from "../constants";
import {
  NowPlayingCard,
  ProgressBar,
  PlaybackControls,
  VolumeSlider,
  ConnectionGuide
} from "../components";
import { usePlaybackControls, useVolumeControl } from "../hooks";

interface NowPlayingContainerProps {
  status: ServiceStatus | null;
  nowPlaying: NowPlayingState | null;
  displayPosition: number;
}

export const NowPlayingContainer: FC<NowPlayingContainerProps> = ({
  status,
  nowPlaying,
  displayPosition
}) => {
  const { isControlling, handlePlayPause, handlePrevious, handleNext } =
    usePlaybackControls();
  const { localVolume, handleVolumeChange } = useVolumeControl(
    nowPlaying?.volume
  );

  // Service not running
  if (!status?.running) {
    return (
      <PanelSection title={STRINGS.SECTION_NOW_PLAYING}>
        <PanelSectionRow>
          <Field label={STRINGS.NP_SERVICE_NOT_RUNNING} />
        </PanelSectionRow>
      </PanelSection>
    );
  }

  // Not connected
  if (!nowPlaying?.connected) {
    return (
      <PanelSection title={STRINGS.SECTION_NOW_PLAYING}>
        <PanelSectionRow>
          <ConnectionGuide />
        </PanelSectionRow>
      </PanelSection>
    );
  }

  // Connected with track
  if (nowPlaying?.track?.name) {
    return (
      <PanelSection title={STRINGS.SECTION_NOW_PLAYING}>
        <PanelSectionRow>
          <NowPlayingCard track={nowPlaying.track} />
        </PanelSectionRow>
        <PanelSectionRow>
          <ProgressBar
            playbackState={nowPlaying.playback_state}
            positionMs={displayPosition}
            durationMs={nowPlaying.track.duration_ms}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <PlaybackControls
            playbackState={nowPlaying.playback_state}
            isDisabled={isControlling}
            onPlayPause={handlePlayPause}
            onPrevious={handlePrevious}
            onNext={handleNext}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <VolumeSlider value={localVolume} onChange={handleVolumeChange} />
        </PanelSectionRow>
      </PanelSection>
    );
  }

  // Connected but no track
  return (
    <PanelSection title={STRINGS.SECTION_NOW_PLAYING}>
      <PanelSectionRow>
        <div style={{ padding: "8px 0", color: COLORS.TEXT_MUTED }}>
          {STRINGS.NP_CONNECTED_NO_TRACK}
        </div>
      </PanelSectionRow>
    </PanelSection>
  );
};
