import { FC } from "react";
import { PanelSection, PanelSectionRow, scrollPanelClasses } from "@decky/ui";
import { STRINGS } from "../constants";
import { LoadingSpinner } from "../components";
import { NowPlayingContainer } from "./NowPlayingContainer";
import { ServiceControlsContainer } from "./ServiceControlsContainer";
import { useServiceStatus, useNowPlaying } from "../hooks";

export const MainContent: FC = () => {
  const {
    status,
    isLoading,
    isToggling,
    isRestarting,
    toggleService,
    restartService
  } = useServiceStatus();

  const { nowPlaying, displayPosition } = useNowPlaying(status?.running ?? false);

  if (isLoading) {
    return (
      <PanelSection title={STRINGS.PLUGIN_TITLE}>
        <PanelSectionRow>
          <LoadingSpinner />
        </PanelSectionRow>
      </PanelSection>
    );
  }

  return (
    <>
      {/* CSS to ensure scroll shows content above focused elements */}
      <style>{`
        .${scrollPanelClasses.ScrollPanel} {
          scroll-padding-top: 200px;
        }
      `}</style>
      <NowPlayingContainer
        status={status}
        nowPlaying={nowPlaying}
        displayPosition={displayPosition}
      />
      <ServiceControlsContainer
        status={status}
        isToggling={isToggling}
        isRestarting={isRestarting}
        onToggle={toggleService}
        onRestart={restartService}
      />
    </>
  );
};
