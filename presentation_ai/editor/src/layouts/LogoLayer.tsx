import React from "react";
import { useTheme } from "./ThemeProvider";

/**
 * Absolutely-positioned logo rendered in one of four corners
 * according to `TemplateTokens.logoPosition`.
 */
export const LogoLayer: React.FC = () => {
  const theme = useTheme();

  if (!theme.logoUrl) return null;

  const positionMap: Record<string, React.CSSProperties> = {
    "top-left": { top: 28, left: 36 },
    "top-right": { top: 28, right: 36 },
    "bottom-left": { bottom: 28, left: 36 },
    "bottom-right": { bottom: 28, right: 36 },
  };

  const pos = positionMap[theme.logoPosition || "bottom-left"];

  return (
    <div
      className="slide-logo-layer"
      style={{
        position: "absolute",
        zIndex: 5,
        ...pos,
        pointerEvents: "none",
      }}
    >
      <img
        src={theme.logoUrl}
        alt="Logo"
        style={{
          maxHeight: 36,
          maxWidth: 120,
          objectFit: "contain",
          opacity: 0.85,
        }}
      />
    </div>
  );
};
