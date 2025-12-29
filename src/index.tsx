import {
  ButtonItem,
  DialogButton,
  PanelSection,
  PanelSectionRow,
  Field,
  ToggleField,
  SliderField,
  TextField,
  Dropdown,
  Spinner,
  Focusable,
  staticClasses
} from "@decky/ui";
import {
  addEventListener,
  removeEventListener,
  callable,
  definePlugin,
  toaster
} from "@decky/api";
import { useState, useEffect, useRef, FC } from "react";
import { FaSpotify, FaCog, FaArrowLeft, FaPlay, FaPause, FaStepBackward, FaStepForward } from "react-icons/fa";

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
  volume: number; // 0.0 to 1.0
}

// Type for settings from backend
interface Settings {
  speaker_name: string;
  bitrate: number;
  device_type: string;
  initial_volume: number;
}

// Define callable functions matching backend methods
const getStatus = callable<[], ServiceStatus>("get_status");
const startSpotifyd = callable<[], boolean>("start_spotifyd");
const stopSpotifyd = callable<[], boolean>("stop_spotifyd");
const enableSpotifyd = callable<[], boolean>("enable_spotifyd");
const disableSpotifyd = callable<[], boolean>("disable_spotifyd");
const restartSpotifyd = callable<[], boolean>("restart_spotifyd");
const getNowPlaying = callable<[], NowPlayingState>("get_now_playing");
const getSettings = callable<[], Settings>("get_settings");
const saveSettings = callable<[string, number, string, number], boolean>("save_settings");

// Playback control methods (via MPRIS)
const playPause = callable<[], boolean>("play_pause");
const nextTrack = callable<[], boolean>("next_track");
const previousTrack = callable<[], boolean>("previous_track");
const setVolume = callable<[number], boolean>("set_volume");

// Format milliseconds to mm:ss
const formatTime = (ms: number): string => {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

// Bitrate options for dropdown
const BITRATE_OPTIONS = [
  { data: 96, label: "96 kbps (Low)" },
  { data: 160, label: "160 kbps (Normal)" },
  { data: 320, label: "320 kbps (High)" }
];

// Device type options for dropdown (must match spotifyd --device-type values)
const DEVICE_TYPE_OPTIONS = [
  { data: "computer", label: "Computer" },
  { data: "tablet", label: "Tablet" },
  { data: "smartphone", label: "Smartphone" },
  { data: "speaker", label: "Speaker" },
  { data: "tv", label: "TV" },
  { data: "avr", label: "AVR (Audio/Video Receiver)" },
  { data: "stb", label: "STB (Set-Top Box)" },
  { data: "audio-dongle", label: "Audio Dongle" },
  { data: "game-console", label: "Game Console" },
  { data: "cast-audio", label: "Cast Audio" },
  { data: "cast-video", label: "Cast Video" },
  { data: "automobile", label: "Automobile" },
  { data: "smartwatch", label: "Smartwatch" },
  { data: "chromebook", label: "Chromebook" },
  { data: "car-thing", label: "Car Thing" },
  { data: "observer", label: "Observer" }
];

// Settings page component
interface SettingsPageProps {
  onBack: () => void;
  serviceStatus: ServiceStatus | null;
  onStatusRefresh: () => Promise<void>;
}

const SettingsPage: FC<SettingsPageProps> = ({ onBack, serviceStatus, onStatusRefresh }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isTogglingAutostart, setIsTogglingAutostart] = useState(false);

  // Local form state
  const [speakerName, setSpeakerName] = useState("");
  const [bitrate, setBitrate] = useState(320);
  const [deviceType, setDeviceType] = useState("speaker");
  const [initialVolume, setInitialVolume] = useState(50);

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const s = await getSettings();
      setSpeakerName(s.speaker_name);
      setBitrate(s.bitrate);
      setDeviceType(s.device_type);
      setInitialVolume(s.initial_volume);
    } catch (error) {
      console.error("Failed to load settings:", error);
      toaster.toast({
        title: "Error",
        body: "Failed to load settings"
      });
    }
    setIsLoading(false);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const success = await saveSettings(speakerName, bitrate, deviceType, initialVolume);
      if (success) {
        toaster.toast({
          title: "Settings saved",
          body: serviceStatus?.running ? "Service restarted with new settings" : "Settings saved successfully"
        });
      } else {
        toaster.toast({
          title: "Error",
          body: "Failed to save settings"
        });
      }
    } catch (error) {
      console.error("Failed to save settings:", error);
      toaster.toast({
        title: "Error",
        body: "Failed to save settings"
      });
    }
    setIsSaving(false);
  };

  // Auto-start toggle handler
  const handleToggleAutostart = async (enabled: boolean) => {
    setIsTogglingAutostart(true);
    try {
      const success = enabled
        ? await enableSpotifyd()
        : await disableSpotifyd();

      if (success) {
        toaster.toast({
          title: "Success",
          body: enabled ? "Auto-start enabled" : "Auto-start disabled"
        });
        await onStatusRefresh();
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

  if (isLoading) {
    return (
      <PanelSection title="Settings">
        <PanelSectionRow>
          <div style={{ display: "flex", justifyContent: "center", padding: "20px" }}>
            <Spinner style={{ width: 24, height: 24 }} />
          </div>
        </PanelSectionRow>
      </PanelSection>
    );
  }

  return (
    <PanelSection title="Settings">
      {/* Back button */}
      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={onBack}
        >
          <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <FaArrowLeft /> Back
          </span>
        </ButtonItem>
      </PanelSectionRow>

      {/* Speaker Name */}
      <PanelSectionRow>
        <TextField
          label="Speaker Name"
          description="Name shown in Spotify's device list"
          value={speakerName}
          onChange={(e) => setSpeakerName(e.target.value)}
        />
      </PanelSectionRow>

      {/* Bitrate */}
      <PanelSectionRow>
        <Field
          label="Bitrate"
          description="Audio quality (higher = better quality, more bandwidth)"
        >
          <Dropdown
            selectedOption={bitrate}
            rgOptions={BITRATE_OPTIONS}
            onChange={(option) => setBitrate(option.data)}
          />
        </Field>
      </PanelSectionRow>

      {/* Device Type */}
      <PanelSectionRow>
        <Field
          label="Device Type"
          description="How this device appears in Spotify"
        >
          <Dropdown
            selectedOption={deviceType}
            rgOptions={DEVICE_TYPE_OPTIONS}
            onChange={(option) => setDeviceType(option.data)}
          />
        </Field>
      </PanelSectionRow>

      {/* Initial Volume */}
      <PanelSectionRow>
        <SliderField
          label="Initial Volume"
          description={`Volume when starting: ${initialVolume}%`}
          value={initialVolume}
          min={0}
          max={100}
          step={1}
          onChange={(value) => setInitialVolume(value)}
          showValue={true}
        />
      </PanelSectionRow>

      {/* Auto-start Toggle */}
      <PanelSectionRow>
        <ToggleField
          label="Auto-start on boot"
          description="Start Spotify Connect when Steam Deck boots"
          checked={serviceStatus?.enabled ?? false}
          disabled={isTogglingAutostart || isSaving}
          onChange={handleToggleAutostart}
        />
      </PanelSectionRow>

      {/* Save Button */}
      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={handleSave}
          disabled={isSaving}
        >
          {isSaving ? (
            <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
              <Spinner style={{ width: 16, height: 16 }} />
              Saving...
            </span>
          ) : (
            "Save Settings"
          )}
        </ButtonItem>
      </PanelSectionRow>
    </PanelSection>
  );
};

const Content: FC = () => {
  // Core state
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [nowPlaying, setNowPlaying] = useState<NowPlayingState | null>(null);

  // Navigation state
  const [showSettings, setShowSettings] = useState<boolean>(false);

  // Local position tracking (simulates playback progress between events)
  const [displayPosition, setDisplayPosition] = useState<number>(0);

  // Operation-specific loading states
  const [isToggling, setIsToggling] = useState<boolean>(false);
  const [isRestarting, setIsRestarting] = useState<boolean>(false);
  const [isControlling, setIsControlling] = useState<boolean>(false);
  const [isAdjustingVolume, setIsAdjustingVolume] = useState<boolean>(false);
  const [localVolume, setLocalVolume] = useState<number>(50);

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

  // Subscribe to now playing updates when service is running
  useEffect(() => {
    if (!status?.running) {
      setNowPlaying(null);
      return;
    }

    // Fetch initial state
    getNowPlaying().then(setNowPlaying).catch(console.error);

    // Listen for real-time updates from backend
    const listener = addEventListener<[NowPlayingState]>(
      "now_playing",
      (state) => setNowPlaying(state)
    );

    return () => removeEventListener("now_playing", listener);
  }, [status?.running]);

  // Simulate playback position progression
  useEffect(() => {
    // Sync position when nowPlaying updates
    if (nowPlaying) {
      setDisplayPosition(nowPlaying.position_ms);
    }
  }, [nowPlaying?.position_ms]);

  // Timer to increment position while playing
  useEffect(() => {
    if (nowPlaying?.playback_state !== "playing" || !nowPlaying?.track) {
      return;
    }

    const interval = setInterval(() => {
      setDisplayPosition((prev) => {
        const newPos = prev + 1000;
        // Cap at track duration
        const duration = nowPlaying.track?.duration_ms || 0;
        return newPos > duration ? duration : newPos;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [nowPlaying?.playback_state, nowPlaying?.track]);

  // Sync local volume with backend when not adjusting
  const volumeTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!isAdjustingVolume && nowPlaying?.volume !== undefined) {
      setLocalVolume(Math.round(nowPlaying.volume * 100));
    }
  }, [nowPlaying?.volume, isAdjustingVolume]);

  // Start/Stop handler
  const handleToggleService = async () => {
    if (!status) return;
    setIsToggling(true);
    try {
      const success = status.running
        ? await stopSpotifyd()
        : await startSpotifyd();

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

  // Restart handler
  const handleRestart = async () => {
    setIsRestarting(true);
    try {
      const success = await restartSpotifyd();
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

  // Playback control handlers
  const handlePlayPause = async () => {
    setIsControlling(true);
    try {
      await playPause();
    } catch (error) {
      console.error("Play/pause error:", error);
    } finally {
      setIsControlling(false);
    }
  };

  const handlePrevious = async () => {
    setIsControlling(true);
    try {
      await previousTrack();
    } catch (error) {
      console.error("Previous track error:", error);
    } finally {
      setIsControlling(false);
    }
  };

  const handleNext = async () => {
    setIsControlling(true);
    try {
      await nextTrack();
    } catch (error) {
      console.error("Next track error:", error);
    } finally {
      setIsControlling(false);
    }
  };

  // Volume change handler with debounce
  const handleVolumeChange = (value: number) => {
    setLocalVolume(value);
    setIsAdjustingVolume(true);

    // Clear existing timeout
    if (volumeTimeoutRef.current) {
      clearTimeout(volumeTimeoutRef.current);
    }

    // Send volume to backend
    const normalizedVolume = value / 100.0;
    setVolume(normalizedVolume).catch((error) => {
      console.error("Volume change error:", error);
    });

    // Reset adjusting state after delay
    volumeTimeoutRef.current = setTimeout(() => {
      setIsAdjustingVolume(false);
    }, 1500);
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
  const isAnyOperationLoading = isToggling || isRestarting;

  // Show settings page if navigated there
  if (showSettings) {
    return (
      <SettingsPage
        onBack={() => setShowSettings(false)}
        serviceStatus={status}
        onStatusRefresh={refreshStatus}
      />
    );
  }

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
        ) : nowPlaying?.track?.name ? (
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
                    {nowPlaying.track.artists?.join(", ") || "Unknown Artist"}
                  </div>
                  <div style={{ color: "#666", fontSize: "11px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {nowPlaying.track.album || "Unknown Album"}
                  </div>
                </div>
              </div>
            </PanelSectionRow>
            {/* Progress bar and time */}
            <PanelSectionRow>
              <div style={{ width: "100%", paddingRight: "16px" }}>
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
                    width: `${(displayPosition / (nowPlaying.track?.duration_ms || 1)) * 100}%`,
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
                  <span>{formatTime(displayPosition)}</span>
                  <span>{formatTime(nowPlaying.track?.duration_ms || 0)}</span>
                </div>
              </div>
            </PanelSectionRow>

            {/* Playback Controls */}
            <PanelSectionRow>
              <Focusable
                style={{
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  gap: "8px",
                  padding: "8px 0",
                  width: "100%"
                }}
                flow-children="horizontal"
              >
                {/* Previous Button */}
                <DialogButton
                  style={{
                    minWidth: "40px",
                    height: "40px",
                    padding: "8px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center"
                  }}
                  onClick={handlePrevious}
                  disabled={isControlling}
                >
                  <FaStepBackward />
                </DialogButton>

                {/* Play/Pause Button */}
                <DialogButton
                  style={{
                    minWidth: "50px",
                    height: "50px",
                    padding: "12px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    background: "#1DB954",
                    borderRadius: "50%"
                  }}
                  onClick={handlePlayPause}
                  disabled={isControlling}
                >
                  {nowPlaying.playback_state === "playing" ? <FaPause /> : <FaPlay style={{ marginLeft: "2px" }} />}
                </DialogButton>

                {/* Next Button */}
                <DialogButton
                  style={{
                    minWidth: "40px",
                    height: "40px",
                    padding: "8px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center"
                  }}
                  onClick={handleNext}
                  disabled={isControlling}
                >
                  <FaStepForward />
                </DialogButton>
              </Focusable>
            </PanelSectionRow>

            {/* Volume Slider */}
            <PanelSectionRow>
              <SliderField
                label="Volume"
                value={localVolume}
                min={0}
                max={100}
                step={1}
                onChange={handleVolumeChange}
                showValue={true}
              />
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

      {/* Settings Button */}
      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={() => setShowSettings(true)}
        >
          <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <FaCog /> Settings
          </span>
        </ButtonItem>
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
