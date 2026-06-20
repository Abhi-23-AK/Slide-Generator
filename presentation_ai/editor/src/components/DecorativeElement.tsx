import React from "react";
import { SlideTheme } from "../utils/themeUtils";

interface DecorativeElementProps {
  theme: SlideTheme;
  position: React.CSSProperties;
}

export const DecorativeElement: React.FC<DecorativeElementProps> = ({ theme, position }) => {
  // PROFESSIONAL: Yellow rectangles/bars
  if (theme.decorativeShape === 'rectangle') {
    return (
      <div style={{
        position: 'absolute',
        width: '20px',
        height: '120px',
        backgroundColor: theme.primary,
        ...position,
      }} />
    );
  }

  // CREATIVE: Hexagon SVG shapes
  if (theme.decorativeShape === 'hexagon') {
    return (
      <svg width="80" height="92" style={{ position: 'absolute', ...position }}>
        <polygon 
          points="40,0 80,20 80,72 40,92 0,72 0,20"
          fill="none" 
          stroke={theme.primary} 
          strokeWidth="2"
        />
      </svg>
    );
  }

  // ACADEMIC: Circle decorations
  if (theme.decorativeShape === 'circle') {
    return (
      <div style={{
        position: 'absolute',
        width: '120px',
        height: '120px',
        borderRadius: '50%',
        backgroundColor: theme.secondary,
        opacity: 0.4,
        ...position,
      }} />
    );
  }

  // TECHNICAL: Glow dot
  if (theme.decorativeShape === 'glow') {
    return (
      <div style={{
        position: 'absolute',
        width: '6px',
        height: '6px',
        borderRadius: '50%',
        backgroundColor: theme.primary,
        boxShadow: theme.glowEffect,
        ...position,
      }} />
    );
  }

  return null;
};
