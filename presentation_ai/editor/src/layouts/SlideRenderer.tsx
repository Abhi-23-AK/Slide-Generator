import React from "react";
import type { Slide, TemplateTokens } from "../types";
import { ThemeProvider } from "./ThemeProvider";
import { SlideFrame } from "./SlideFrame";
import { EditingOverlay } from "./EditingOverlay";
import "./layouts.css";

interface SlideRendererProps {
  /** The slide data to render */
  slide: Slide;
  /** 1-based slide index */
  slideNumber: number;
  /** Total slides in the deck */
  totalSlides: number;
  /** Optional theme token overrides from the deck */
  theme?: Partial<TemplateTokens>;
  /** Whether the user is in canvas-editing mode (shows editing overlay) */
  editing?: boolean;
  /** Children rendered inside EditingOverlay (drag handles, selection outlines, etc.) */
  editingChildren?: React.ReactNode;
  /** Manual zoom level */
  zoom?: number;
}

/**
 * Top-level rendering component for a single slide.
 *
 * Architecture:
 * ```
 * SlideRenderer
 *   ├── ThemeProvider (CSS variables from TemplateTokens)
 *   ├── SlideFrame (1920×1080 viewport, scaled to screen)
 *   │   ├── BackgroundLayer (image/color/gradient)
 *   │   ├── ContentLayer → {HeroSlide | TwoColumnSlide | ...}
 *   │   ├── FooterLayer (slide number, footer text)
 *   │   ├── LogoLayer (absolute positioned, from template zone)
 *   │   └── EditingOverlay (optional, for editor UX)
 * ```
 */
export const SlideRenderer: React.FC<SlideRendererProps> = ({
  slide,
  slideNumber,
  totalSlides,
  theme,
  editing = false,
  editingChildren,
  zoom = 1,
}) => {
  return (
    <ThemeProvider tokens={theme}>
      <SlideFrame
        slide={slide}
        slideNumber={slideNumber}
        totalSlides={totalSlides}
        zoom={zoom}
      >
        <EditingOverlay active={editing}>
          {editingChildren}
        </EditingOverlay>
      </SlideFrame>
    </ThemeProvider>
  );
};
