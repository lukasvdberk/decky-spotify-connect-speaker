import { FC } from "react";
import { STRINGS, COLORS } from "../constants";

export const ConnectionGuide: FC = () => {
  return (
    <div style={{ padding: "8px 0", color: COLORS.TEXT_SECONDARY }}>
      <div style={{ fontWeight: "bold", marginBottom: "8px" }}>
        {STRINGS.NP_WAITING_CONNECTION}
      </div>
      <div style={{
        fontSize: "12px",
        lineHeight: "1.6",
        color: COLORS.TEXT_MUTED
      }}>
        {STRINGS.GUIDE_STEP_1}<br />
        {STRINGS.GUIDE_STEP_2}<br />
        {STRINGS.GUIDE_STEP_3}<br />
        {STRINGS.GUIDE_STEP_4}
      </div>
    </div>
  );
};
