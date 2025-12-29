import { useState, useEffect, useCallback } from "react";
import { toaster } from "@decky/api";
import type { ServiceStatus } from "../types";
import { STRINGS } from "../constants";
import * as api from "../api";

interface UseSettingsReturn {
  isLoading: boolean;
  isSaving: boolean;
  isTogglingAutostart: boolean;
  serviceStatus: ServiceStatus | null;
  speakerName: string;
  bitrate: number;
  deviceType: string;
  initialVolume: number;
  setSpeakerName: (value: string) => void;
  setBitrate: (value: number) => void;
  setDeviceType: (value: string) => void;
  setInitialVolume: (value: number) => void;
  handleSave: () => Promise<void>;
  handleToggleAutostart: (enabled: boolean) => Promise<void>;
}

export const useSettings = (): UseSettingsReturn => {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isTogglingAutostart, setIsTogglingAutostart] = useState(false);
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus | null>(null);

  // Form state
  const [speakerName, setSpeakerName] = useState("");
  const [bitrate, setBitrate] = useState(320);
  const [deviceType, setDeviceType] = useState("speaker");
  const [initialVolume, setInitialVolume] = useState(50);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [settings, status] = await Promise.all([
        api.getSettings(),
        api.getStatus()
      ]);
      setSpeakerName(settings.speaker_name);
      setBitrate(settings.bitrate);
      setDeviceType(settings.device_type);
      setInitialVolume(settings.initial_volume);
      setServiceStatus(status);
    } catch (error) {
      console.error("Failed to load settings:", error);
      toaster.toast({
        title: STRINGS.TOAST_ERROR,
        body: STRINGS.TOAST_FAILED_LOAD_SETTINGS
      });
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSave = useCallback(async () => {
    setIsSaving(true);
    try {
      const success = await api.saveSettings(
        speakerName,
        bitrate,
        deviceType,
        initialVolume
      );
      if (success) {
        toaster.toast({
          title: STRINGS.TOAST_SETTINGS_SAVED,
          body: serviceStatus?.running
            ? STRINGS.TOAST_SETTINGS_SAVED_RESTARTED
            : STRINGS.TOAST_SETTINGS_SAVED_SUCCESS
        });
      } else {
        toaster.toast({
          title: STRINGS.TOAST_ERROR,
          body: STRINGS.TOAST_FAILED_SAVE
        });
      }
    } catch (error) {
      console.error("Failed to save settings:", error);
      toaster.toast({
        title: STRINGS.TOAST_ERROR,
        body: STRINGS.TOAST_FAILED_SAVE
      });
    }
    setIsSaving(false);
  }, [speakerName, bitrate, deviceType, initialVolume, serviceStatus?.running]);

  const handleToggleAutostart = useCallback(async (enabled: boolean) => {
    setIsTogglingAutostart(true);
    try {
      const success = enabled
        ? await api.enableSpotifyd()
        : await api.disableSpotifyd();

      if (success) {
        toaster.toast({
          title: STRINGS.TOAST_SUCCESS,
          body: enabled
            ? STRINGS.TOAST_AUTOSTART_ENABLED
            : STRINGS.TOAST_AUTOSTART_DISABLED
        });
        // Refresh status
        const status = await api.getStatus();
        setServiceStatus(status);
      } else {
        toaster.toast({
          title: STRINGS.TOAST_ERROR,
          body: enabled
            ? STRINGS.TOAST_FAILED_AUTOSTART_ENABLE
            : STRINGS.TOAST_FAILED_AUTOSTART_DISABLE
        });
      }
    } catch (error) {
      console.error("Toggle autostart error:", error);
      toaster.toast({
        title: STRINGS.TOAST_ERROR,
        body: STRINGS.TOAST_OPERATION_FAILED
      });
    } finally {
      setIsTogglingAutostart(false);
    }
  }, []);

  return {
    isLoading,
    isSaving,
    isTogglingAutostart,
    serviceStatus,
    speakerName,
    bitrate,
    deviceType,
    initialVolume,
    setSpeakerName,
    setBitrate,
    setDeviceType,
    setInitialVolume,
    handleSave,
    handleToggleAutostart
  };
};
