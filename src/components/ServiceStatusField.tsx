import { FC } from "react";
import { Field } from "@decky/ui";
import type { ServiceStatus } from "../types";
import { STRINGS, COLORS } from "../constants";

interface ServiceStatusFieldProps {
  status: ServiceStatus | null;
}

export const ServiceStatusField: FC<ServiceStatusFieldProps> = ({ status }) => {
  return (
    <Field
      label={STRINGS.LABEL_STATUS}
      description={status?.state || STRINGS.STATUS_UNKNOWN}
    >
      <span style={{
        color: status?.running ? COLORS.SPOTIFY_GREEN : COLORS.STATUS_STOPPED,
        fontWeight: "bold"
      }}>
        {status?.running ? STRINGS.STATUS_RUNNING : STRINGS.STATUS_STOPPED}
      </span>
    </Field>
  );
};
