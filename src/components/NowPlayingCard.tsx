import { FC } from "react";
import type { TrackInfo } from "../types";
import { STRINGS, COLORS } from "../constants";

interface NowPlayingCardProps {
  track: TrackInfo;
}

export const NowPlayingCard: FC<NowPlayingCardProps> = ({ track }) => {
  return (
    <div style={{
      display: "flex",
      gap: "12px",
      alignItems: "center",
      padding: "8px 0"
    }}>
      {track.cover_url && (
        <img
          src={track.cover_url}
          alt="Album art"
          style={{
            width: 64,
            height: 64,
            borderRadius: 4,
            flexShrink: 0
          }}
        />
      )}
      <div style={{ minWidth: 0, flex: 1 }}>
        <div style={{
          fontWeight: "bold",
          color: COLORS.TEXT_PRIMARY,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap"
        }}>
          {track.name}
        </div>
        <div style={{
          color: COLORS.TEXT_SECONDARY,
          fontSize: "12px",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap"
        }}>
          {track.artists?.join(", ") || STRINGS.NP_UNKNOWN_ARTIST}
        </div>
        <div style={{
          color: COLORS.TEXT_VERY_MUTED,
          fontSize: "11px",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap"
        }}>
          {track.album || STRINGS.NP_UNKNOWN_ALBUM}
        </div>
      </div>
    </div>
  );
};
