import { FC } from "react";
import {
  TextField,
  DropdownItem,
  SliderField,
  ToggleField,
  ButtonItem,
  Spinner
} from "@decky/ui";
import { STRINGS, BITRATE_OPTIONS, DEVICE_TYPE_OPTIONS } from "../constants";

interface SettingsFormProps {
  speakerName: string;
  bitrate: number;
  deviceType: string;
  initialVolume: number;
  autostartEnabled: boolean;
  isSaving: boolean;
  isTogglingAutostart: boolean;
  onSpeakerNameChange: (value: string) => void;
  onBitrateChange: (value: number) => void;
  onDeviceTypeChange: (value: string) => void;
  onInitialVolumeChange: (value: number) => void;
  onAutostartToggle: (enabled: boolean) => void;
  onSave: () => void;
}

export const SettingsForm: FC<SettingsFormProps> = ({
  speakerName,
  bitrate,
  deviceType,
  initialVolume,
  autostartEnabled,
  isSaving,
  isTogglingAutostart,
  onSpeakerNameChange,
  onBitrateChange,
  onDeviceTypeChange,
  onInitialVolumeChange,
  onAutostartToggle,
  onSave
}) => {
  return (
    <>
      <TextField
        label={STRINGS.LABEL_SPEAKER_NAME}
        value={speakerName}
        onChange={(e) => onSpeakerNameChange(e.target.value)}
      />

      <DropdownItem
        label={STRINGS.LABEL_BITRATE}
        rgOptions={BITRATE_OPTIONS}
        selectedOption={bitrate}
        onChange={(option) => onBitrateChange(option.data)}
      />

      <DropdownItem
        label={STRINGS.LABEL_DEVICE_TYPE}
        rgOptions={DEVICE_TYPE_OPTIONS}
        selectedOption={deviceType}
        onChange={(option) => onDeviceTypeChange(option.data)}
      />

      <SliderField
        label={`Initial Volume: ${initialVolume}%`}
        value={initialVolume}
        min={0}
        max={100}
        step={1}
        onChange={onInitialVolumeChange}
      />

      <ToggleField
        label={STRINGS.LABEL_AUTOSTART}
        checked={autostartEnabled}
        disabled={isTogglingAutostart || isSaving}
        onChange={onAutostartToggle}
      />

      <ButtonItem
        layout="below"
        onClick={onSave}
        disabled={isSaving}
      >
        {isSaving ? (
          <span style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "8px"
          }}>
            <Spinner style={{ width: 16, height: 16 }} />
            {STRINGS.LOADING_SAVING}
          </span>
        ) : (
          STRINGS.BTN_SAVE_SETTINGS
        )}
      </ButtonItem>
    </>
  );
};
