import { FC } from "react";
import { SliderField } from "@decky/ui";
import { STRINGS } from "../constants";

interface VolumeSliderProps {
  value: number;
  onChange: (value: number) => void;
}

export const VolumeSlider: FC<VolumeSliderProps> = ({ value, onChange }) => {
  return (
    <SliderField
      label={STRINGS.LABEL_VOLUME}
      value={value}
      min={0}
      max={100}
      step={1}
      onChange={onChange}
      showValue={true}
    />
  );
};
