import { FC } from "react";
import { PanelSection, PanelSectionRow, ButtonItem, Spinner, Router } from "@decky/ui";
import { FaCog } from "react-icons/fa";
import type { ServiceStatus } from "../types";
import { STRINGS, ROUTES } from "../constants";
import { ServiceStatusField } from "../components";

interface ServiceControlsContainerProps {
  status: ServiceStatus | null;
  isToggling: boolean;
  isRestarting: boolean;
  onToggle: () => void;
  onRestart: () => void;
}

export const ServiceControlsContainer: FC<ServiceControlsContainerProps> = ({
  status,
  isToggling,
  isRestarting,
  onToggle,
  onRestart
}) => {
  const isAnyOperationLoading = isToggling || isRestarting;
  const isRunning = status?.running ?? false;

  const handleOpenSettings = () => {
    Router.CloseSideMenus();
    Router.Navigate(ROUTES.SETTINGS);
  };

  return (
    <PanelSection title={STRINGS.SECTION_SERVICE_CONTROLS}>
      <PanelSectionRow>
        <ServiceStatusField status={status} />
      </PanelSectionRow>

      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={onToggle}
          disabled={isAnyOperationLoading}
        >
          {isToggling ? (
            <span style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px"
            }}>
              <Spinner style={{ width: 16, height: 16 }} />
              {isRunning ? STRINGS.LOADING_STOPPING : STRINGS.LOADING_STARTING}
            </span>
          ) : (
            isRunning ? STRINGS.BTN_STOP_SERVICE : STRINGS.BTN_START_SERVICE
          )}
        </ButtonItem>
      </PanelSectionRow>

      {isRunning && (
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            onClick={onRestart}
            disabled={isAnyOperationLoading}
          >
            {isRestarting ? (
              <span style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px"
              }}>
                <Spinner style={{ width: 16, height: 16 }} />
                {STRINGS.LOADING_RESTARTING}
              </span>
            ) : (
              STRINGS.BTN_RESTART_SERVICE
            )}
          </ButtonItem>
        </PanelSectionRow>
      )}

      <PanelSectionRow>
        <ButtonItem layout="below" onClick={handleOpenSettings}>
          <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <FaCog /> {STRINGS.BTN_SETTINGS}
          </span>
        </ButtonItem>
      </PanelSectionRow>
    </PanelSection>
  );
};
