import { FC } from "react";
import { Spinner } from "@decky/ui";

interface LoadingSpinnerProps {
  size?: "small" | "medium" | "large";
  centered?: boolean;
  padding?: string;
}

const SIZE_MAP = {
  small: 16,
  medium: 24,
  large: 32
};

export const LoadingSpinner: FC<LoadingSpinnerProps> = ({
  size = "medium",
  centered = true,
  padding = "20px"
}) => {
  const dimension = SIZE_MAP[size];

  return (
    <div style={{
      display: centered ? "flex" : "block",
      justifyContent: centered ? "center" : undefined,
      padding
    }}>
      <Spinner style={{ width: dimension, height: dimension }} />
    </div>
  );
};
