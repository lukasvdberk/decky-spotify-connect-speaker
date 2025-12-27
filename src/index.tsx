import {
  ButtonItem,
  PanelSection,
  PanelSectionRow,
  Field,
  ToggleField,
  Spinner,
  staticClasses
} from "@decky/ui";
import {
  callable,
  definePlugin,
  toaster
} from "@decky/api";
import { useState, useEffect, FC } from "react";
import { FaSpotify } from "react-icons/fa";

// Type for status response from backend
interface ServiceStatus {
  running: boolean;
  enabled: boolean;
  service: string;
  state: string;
}

// Define callable functions matching backend methods
const getStatus = callable<[], ServiceStatus>("get_status");
const startLibrespot = callable<[], boolean>("start_librespot");
const stopLibrespot = callable<[], boolean>("stop_librespot");
const enableLibrespot = callable<[], boolean>("enable_librespot");
const disableLibrespot = callable<[], boolean>("disable_librespot");
const restartLibrespot = callable<[], boolean>("restart_librespot");

const Content: FC = () => {
  // Core state
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Operation-specific loading states
  const [isToggling, setIsToggling] = useState<boolean>(false);
  const [isTogglingAutostart, setIsTogglingAutostart] = useState<boolean>(false);
  const [isRestarting, setIsRestarting] = useState<boolean>(false);

  // Refresh status from backend
  const refreshStatus = async () => {
    try {
      const newStatus = await getStatus();
      setStatus(newStatus);
    } catch (error) {
      console.error("Failed to get status:", error);
      toaster.toast({
        title: "Error",
        body: "Failed to get service status"
      });
    }
  };

  // Initial load
  useEffect(() => {
    const loadInitialStatus = async () => {
      setIsLoading(true);
      await refreshStatus();
      setIsLoading(false);
    };
    loadInitialStatus();
  }, []);

  // Start/Stop handler
  const handleToggleService = async () => {
    if (!status) return;
    setIsToggling(true);
    try {
      const success = status.running
        ? await stopLibrespot()
        : await startLibrespot();

      if (success) {
        toaster.toast({
          title: "Success",
          body: status.running ? "Spotify speaker stopped" : "Spotify speaker started"
        });
        await refreshStatus();
      } else {
        toaster.toast({
          title: "Error",
          body: `Failed to ${status.running ? "stop" : "start"} service`
        });
      }
    } catch (error) {
      console.error("Toggle service error:", error);
      toaster.toast({
        title: "Error",
        body: "Operation failed"
      });
    } finally {
      setIsToggling(false);
    }
  };

  // Auto-start toggle handler
  const handleToggleAutostart = async (enabled: boolean) => {
    setIsTogglingAutostart(true);
    try {
      const success = enabled
        ? await enableLibrespot()
        : await disableLibrespot();

      if (success) {
        toaster.toast({
          title: "Success",
          body: enabled ? "Auto-start enabled" : "Auto-start disabled"
        });
        await refreshStatus();
      } else {
        toaster.toast({
          title: "Error",
          body: `Failed to ${enabled ? "enable" : "disable"} auto-start`
        });
      }
    } catch (error) {
      console.error("Toggle autostart error:", error);
      toaster.toast({
        title: "Error",
        body: "Operation failed"
      });
    } finally {
      setIsTogglingAutostart(false);
    }
  };

  // Restart handler
  const handleRestart = async () => {
    setIsRestarting(true);
    try {
      const success = await restartLibrespot();
      if (success) {
        toaster.toast({
          title: "Success",
          body: "Spotify speaker restarted"
        });
        await refreshStatus();
      } else {
        toaster.toast({
          title: "Error",
          body: "Failed to restart service"
        });
      }
    } catch (error) {
      console.error("Restart error:", error);
      toaster.toast({
        title: "Error",
        body: "Restart failed"
      });
    } finally {
      setIsRestarting(false);
    }
  };

  // Loading state for initial load
  if (isLoading) {
    return (
      <PanelSection title="Spotify Connect">
        <PanelSectionRow>
          <div style={{ display: "flex", justifyContent: "center", padding: "20px" }}>
            <Spinner style={{ width: 24, height: 24 }} />
          </div>
        </PanelSectionRow>
      </PanelSection>
    );
  }

  // Determine if any operation is in progress
  const isAnyOperationLoading = isToggling || isTogglingAutostart || isRestarting;

  return (
    <PanelSection title="Spotify Connect">
      {/* Status Display */}
      <PanelSectionRow>
        <Field
          label="Status"
          description={status?.state || "unknown"}
        >
          <span style={{
            color: status?.running ? "#1DB954" : "#888888",
            fontWeight: "bold"
          }}>
            {status?.running ? "Running" : "Stopped"}
          </span>
        </Field>
      </PanelSectionRow>

      {/* Start/Stop Button */}
      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={handleToggleService}
          disabled={isAnyOperationLoading}
        >
          {isToggling ? (
            <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
              <Spinner style={{ width: 16, height: 16 }} />
              {status?.running ? "Stopping..." : "Starting..."}
            </span>
          ) : (
            status?.running ? "Stop Service" : "Start Service"
          )}
        </ButtonItem>
      </PanelSectionRow>

      {/* Restart Button - only show when running */}
      {status?.running && (
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            onClick={handleRestart}
            disabled={isAnyOperationLoading}
          >
            {isRestarting ? (
              <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
                <Spinner style={{ width: 16, height: 16 }} />
                Restarting...
              </span>
            ) : (
              "Restart Service"
            )}
          </ButtonItem>
        </PanelSectionRow>
      )}

      {/* Auto-start Toggle */}
      <PanelSectionRow>
        <ToggleField
          label="Auto-start on boot"
          description="Start Spotify Connect when Steam Deck boots"
          checked={status?.enabled ?? false}
          disabled={isAnyOperationLoading}
          onChange={handleToggleAutostart}
        />
      </PanelSectionRow>
    </PanelSection>
  );
};

export default definePlugin(() => {
  console.log("Spotify Connect Speaker plugin initializing");

  return {
    name: "Spotify Connect Speaker",
    titleView: (
      <div className={staticClasses.Title}>
        <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <FaSpotify />
          Spotify Connect
        </span>
      </div>
    ),
    content: <Content />,
    icon: <FaSpotify />,
    onDismount() {
      console.log("Spotify Connect Speaker plugin unloading");
    },
  };
});
