/* ═══════════════════════════════════════════════════
   Barrel exports for the layout / renderer system
   ═══════════════════════════════════════════════════ */

// Top-level renderer
export { SlideRenderer } from "./SlideRenderer";

// Architecture layers
export { ThemeProvider, useTheme, DEFAULT_TOKENS } from "./ThemeProvider";
export { SlideFrame } from "./SlideFrame";
export { BackgroundLayer } from "./BackgroundLayer";
export { LogoLayer } from "./LogoLayer";
export { FooterLayer } from "./FooterLayer";
export { ContentLayer } from "./ContentLayer";
export { EditingOverlay } from "./EditingOverlay";

// Legacy renderer
export { LayoutRenderer } from "./LayoutRenderer";

// Individual slide layouts
export { HeroLayout } from "./HeroLayout";
export { OneColumnLayout } from "./OneColumnLayout";
export { TwoColumnLayout } from "./TwoColumnLayout";
export { ThreeColumnLayout } from "./ThreeColumnLayout";
export { FourGridLayout } from "./FourGridLayout";
export { DashboardLayout } from "./DashboardLayout";
export { ArchitectureLayout } from "./ArchitectureLayout";
export { TimelineLayout } from "./TimelineLayout";
export { ComparisonSlide } from "./ComparisonSlide";
export { ProcessSlide } from "./ProcessSlide";

// Neumorphism layouts
export { NeuroHeroLayout } from "./neumorphism/NeuroHeroLayout";
export { NeuroDashboardLayout } from "./neumorphism/NeuroDashboardLayout";
export { NeuroProcessLayout } from "./neumorphism/NeuroProcessLayout";
export { NeuroTimelineLayout } from "./neumorphism/NeuroTimelineLayout";
export { NeuroComparisonLayout } from "./neumorphism/NeuroComparisonLayout";

