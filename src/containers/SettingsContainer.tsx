import { FC } from "react";
import { DialogBody, DialogControlsSection, DialogControlsSectionHeader } from "@decky/ui";
import { STRINGS } from "../constants";
import { LoadingSpinner, SettingsForm } from "../components";
import { useSettings } from "../hooks";

export const SettingsContainer: FC = () => {
  const {
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
  } = useSettings();

  if (isLoading) {
    return (
      <DialogBody>
        <DialogControlsSection>
          <LoadingSpinner size="large" padding="40px" />
        </DialogControlsSection>
      </DialogBody>
    );
  }

  return (
    <div style={{ padding: "16px 24px" }}>
      <DialogControlsSection>
        <DialogControlsSectionHeader>
          {STRINGS.SECTION_SPEAKER_SETTINGS}
        </DialogControlsSectionHeader>

        <SettingsForm
          speakerName={speakerName}
          bitrate={bitrate}
          deviceType={deviceType}
          initialVolume={initialVolume}
          autostartEnabled={serviceStatus?.enabled ?? false}
          isSaving={isSaving}
          isTogglingAutostart={isTogglingAutostart}
          onSpeakerNameChange={setSpeakerName}
          onBitrateChange={setBitrate}
          onDeviceTypeChange={setDeviceType}
          onInitialVolumeChange={setInitialVolume}
          onAutostartToggle={handleToggleAutostart}
          onSave={handleSave}
        />
      </DialogControlsSection>
    </div>
  );
};
