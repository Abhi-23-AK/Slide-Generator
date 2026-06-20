import React from "react";

interface BackgroundLayerProps {
  /** Slide background value – hex colour, CSS gradient, or image URL */
  background: string;
  /** Optional zone_content.background_image override */
  backgroundImage?: string;
}

/**
 * Renders the full-bleed background behind all other slide layers.
 * Accepts solid colours, CSS gradients, or image URLs.
 */
export const BackgroundLayer: React.FC<BackgroundLayerProps> = ({
  background,
  backgroundImage,
}) => {
  const style: React.CSSProperties = {
    position: "absolute",
    inset: 0,
    zIndex: 0,
  };

  if (backgroundImage) {
    style.backgroundImage = `url(${backgroundImage})`;
    style.backgroundSize = "cover";
    style.backgroundPosition = "center";
  } else if (background.startsWith("http") || background.startsWith("data:")) {
    style.backgroundImage = `url(${background})`;
    style.backgroundSize = "cover";
    style.backgroundPosition = "center";
  } else if (background.includes("gradient") || background.includes("linear") || background.includes("radial")) {
    style.background = background;
  } else {
    style.backgroundColor = background || "var(--theme-colorBackground, #ffffff)";
  }

  return <div className="slide-background-layer" style={style} />;
};
