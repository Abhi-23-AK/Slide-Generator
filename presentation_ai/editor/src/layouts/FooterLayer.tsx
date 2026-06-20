import React from "react";
import { useTheme } from "./ThemeProvider";

interface FooterLayerProps {
  /** 1-based slide number */
  slideNumber: number;
  /** Total number of slides in deck */
  totalSlides: number;
}

/**
 * Footer bar pinned to the bottom of the slide frame showing
 * optional footer text (from theme) and slide numbering.
 */
export const FooterLayer: React.FC<FooterLayerProps> = ({
  slideNumber,
  totalSlides,
}) => {
  const theme = useTheme();

  return (
    <div
      className="slide-footer-layer"
      style={{
        position: "absolute",
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 4,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 40px",
        height: 36,
        fontSize: 11,
        fontWeight: 500,
        fontFamily: "var(--theme-fontBody, inherit)",
        color: "var(--theme-colorTextMuted, #64748b)",
        background: "linear-gradient(to top, rgba(0,0,0,0.04), transparent)",
        pointerEvents: "none",
        letterSpacing: "0.02em",
      }}
    >
      <span style={{ opacity: 0.7 }}>{theme.footerText || ""}</span>
      <span style={{ opacity: 0.6, fontVariantNumeric: "tabular-nums" }}>
        {slideNumber} / {totalSlides}
      </span>
    </div>
  );
};
