import React from "react";
import type { Slide } from "../types";
import { OneColumnLayout } from "./OneColumnLayout";
import { TwoColumnLayout } from "./TwoColumnLayout";
import { ThreeColumnLayout } from "./ThreeColumnLayout";
import { FourGridLayout } from "./FourGridLayout";
import { HeroLayout } from "./HeroLayout";
import { DashboardLayout } from "./DashboardLayout";
import { ArchitectureLayout } from "./ArchitectureLayout";
import { TimelineLayout } from "./TimelineLayout";
import { ComparisonSlide } from "./ComparisonSlide";
import { ProcessSlide } from "./ProcessSlide";
import { useTheme } from "./ThemeProvider";
import { getTheme } from "../utils/themeUtils";

// Neumorphism imports
import { NeuroHeroLayout } from "./neumorphism/NeuroHeroLayout";
import { NeuroDashboardLayout } from "./neumorphism/NeuroDashboardLayout";
import { NeuroProcessLayout } from "./neumorphism/NeuroProcessLayout";
import { NeuroTimelineLayout } from "./neumorphism/NeuroTimelineLayout";
import { NeuroComparisonLayout } from "./neumorphism/NeuroComparisonLayout";

interface ContentLayerProps {
  slide: Slide;
}

/**
 * Selects and renders the appropriate layout component for the
 * slide's `layout_id`. Sits inside SlideFrame above the background
 * but below the editing overlay.
 */
export const ContentLayer: React.FC<ContentLayerProps> = ({ slide }) => {
  const layoutId = slide.layout_id;
  const tokens = useTheme();
  const theme = getTheme(tokens.tone || slide.background || "professional");

  if (!layoutId) return null;

  const style: React.CSSProperties = {
    position: "relative",
    zIndex: 2,
    width: "100%",
    height: "100%",
  };

  const component = (() => {
    const isNeuro = theme.tone === "neumorphism";

    switch (layoutId) {
      case "OneColumn":
        return <OneColumnLayout slide={slide} theme={theme} />;
      case "TwoColumn":
        return <TwoColumnLayout slide={slide} theme={theme} />;
      case "ThreeColumn":
        return <ThreeColumnLayout slide={slide} theme={theme} />;
      case "FourGrid":
        return <FourGridLayout slide={slide} theme={theme} />;
      case "Hero":
        return isNeuro ? <NeuroHeroLayout slide={slide} theme={theme} /> : <HeroLayout slide={slide} theme={theme} />;
      case "Dashboard":
        return isNeuro ? <NeuroDashboardLayout slide={slide} theme={theme} /> : <DashboardLayout slide={slide} theme={theme} />;
      case "Architecture":
        return <ArchitectureLayout slide={slide} theme={theme} />;
      case "Timeline":
        return isNeuro ? <NeuroTimelineLayout slide={slide} theme={theme} /> : <TimelineLayout slide={slide} theme={theme} />;
      case "Comparison":
        return isNeuro ? <NeuroComparisonLayout slide={slide} theme={theme} /> : <ComparisonSlide slide={slide} theme={theme} />;
      case "Process":
        return isNeuro ? <NeuroProcessLayout slide={slide} theme={theme} /> : <ProcessSlide slide={slide} theme={theme} />;
      default:
        return null;
    }
  })();

  return <div className="slide-content-layer" style={style}>{component}</div>;
};
