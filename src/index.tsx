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

// Type for now playing state from backend
interface NowPlayingState {
  connected: boolean;
  user_name: string | null;
  connection_id: string | null;
  track: {
    name: string;
    artists: string[];
    album: string;
    cover_url: string;
    duration_ms: number;
  } | null;
  playback_state: "playing" | "paused" | "stopped";
  position_ms: number;
}

// Define callable functions matching backend methods
const getStatus = callable<[], ServiceStatus>("get_status");
const startLibrespot = callable<[], boolean>("start_librespot");
const stopLibrespot = callable<[], boolean>("stop_librespot");
const enableLibrespot = callable<[], boolean>("enable_librespot");
const disableLibrespot = callable<[], boolean>("disable_librespot");
const restartLibrespot = callable<[], boolean>("restart_librespot");
const getNowPlaying = callable<[], NowPlayingState>("get_now_playing");

// Format milliseconds to mm:ss
const formatTime = (ms: number): string => {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

const Content: FC = () => {
  // Core state
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [nowPlaying, setNowPlaying] = useState<NowPlayingState | null>(null);

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

  // Poll for now playing state when service is running
  useEffect(() => {
    if (!status?.running) {
      setNowPlaying(null);
      return;
    }

    const poll = async () => {
      try {
        const np = await getNowPlaying();
        setNowPlaying(np);
      } catch (e) {
        console.error("Failed to get now playing:", e);
      }
    };

    poll(); // Initial fetch
    const interval = setInterval(poll, 2000);
    return () => clearInterval(interval);
  }, [status?.running]);

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
    <>
      {/* Now Playing Section */}
      <PanelSection title="Now Playing">
        {!status?.running ? (
          <PanelSectionRow>
            <Field label="Service not running" />
          </PanelSectionRow>
        ) : !nowPlaying?.connected ? (
          <PanelSectionRow>
            <div style={{ padding: "8px 0", color: "#b8bcbf" }}>
              <div style={{ fontWeight: "bold", marginBottom: "8px" }}>
                Waiting for connection...
              </div>
              <div style={{ fontSize: "12px", lineHeight: "1.6", color: "#888" }}>
                1. Open Spotify on your phone or computer<br/>
                2. Play any song<br/>
                3. Tap the "Devices" icon<br/>
                4. Select "decky-spotify"
              </div>
            </div>
          </PanelSectionRow>
        ) : nowPlaying?.track ? (
          <>
            <PanelSectionRow>
              <div style={{ display: "flex", gap: "12px", alignItems: "center", padding: "8px 0" }}>
                {nowPlaying.track.cover_url && (
                  <img
                    src={nowPlaying.track.cover_url}
                    alt="Album art"
                    style={{ width: 64, height: 64, borderRadius: 4, flexShrink: 0 }}
                  />
                )}
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ fontWeight: "bold", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {nowPlaying.track.name}
                  </div>
                  <div style={{ color: "#888", fontSize: "12px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {nowPlaying.track.artists.join(", ")}
                  </div>
                  <div style={{ color: "#666", fontSize: "11px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {nowPlaying.track.album}
                  </div>
                </div>
              </div>
            </PanelSectionRow>
            {/* Progress bar and time */}
            <PanelSectionRow>
              <div style={{ width: "100%" }}>
                {/* Playback state indicator */}
                <div style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "6px"
                }}>
                  <span style={{
                    color: nowPlaying.playback_state === "playing" ? "#1DB954" : "#888",
                    fontSize: "12px",
                    fontWeight: "bold"
                  }}>
                    {nowPlaying.playback_state === "playing" ? "▶ Playing" : "⏸ Paused"}
                  </span>
                </div>

                {/* Progress bar */}
                <div style={{
                  width: "100%",
                  height: "4px",
                  backgroundColor: "#23262e",
                  borderRadius: "2px",
                  overflow: "hidden"
                }}>
                  <div style={{
                    width: `${(nowPlaying.position_ms / (nowPlaying.track?.duration_ms || 1)) * 100}%`,
                    height: "100%",
                    backgroundColor: "#1DB954",
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
                  color: "#888"
                }}>
                  <span>{formatTime(nowPlaying.position_ms)}</span>
                  <span>{formatTime(nowPlaying.track?.duration_ms || 0)}</span>
                </div>
              </div>
            </PanelSectionRow>
          </>
        ) : (
          <PanelSectionRow>
            <div style={{ padding: "8px 0", color: "#888" }}>
              Connected - No track playing
            </div>
          </PanelSectionRow>
        )}
      </PanelSection>

      <PanelSection title="Service Controls">
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
    </>
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
