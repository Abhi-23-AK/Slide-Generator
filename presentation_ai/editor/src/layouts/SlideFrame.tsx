import React, { useRef, useEffect, useState, useCallback } from "react";
import type { Slide } from "../types";
import { BackgroundLayer } from "./BackgroundLayer";
import { LogoLayer } from "./LogoLayer";
import { FooterLayer } from "./FooterLayer";
import { ContentLayer } from "./ContentLayer";

/** Canonical presentation viewport */
const FRAME_W = 1920;
const FRAME_H = 1080;

interface SlideFrameProps {
  slide: Slide;
  slideNumber: number;
  totalSlides: number;
  zoom?: number;
  children?: React.ReactNode;
}

/**
 * SlideFrame maintains a 1920×1080 internal coordinate system and
 * auto-scales to fit within its parent container using transform: scale().
 * It layers Background → Content → Logo → Footer from bottom to top.
 */
export const SlideFrame: React.FC<SlideFrameProps> = ({
  slide,
  slideNumber,
  totalSlides,
  zoom = 1,
  children,
}) => {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  const recalcScale = useCallback(() => {
    const el = wrapperRef.current;
    if (!el) return;
    const stage = el.closest(".canvas-stage") || el.parentElement;
    if (!stage) return;
    const sw = (stage.clientWidth - 88) / FRAME_W;
    const sh = (stage.clientHeight - 88) / FRAME_H;
    setScale(Math.min(sw, sh, 1));
  }, []);

  useEffect(() => {
    recalcScale();
    const el = wrapperRef.current;
    const stage = el?.closest(".canvas-stage") || el?.parentElement;
    if (!stage) return;
    const ro = new ResizeObserver(recalcScale);
    ro.observe(stage);
    return () => ro.disconnect();
  }, [recalcScale]);

  const bgImage = slide.zone_content?.background_image;
  const finalScale = scale * zoom;

  return (
    <div
      className="slide-scale-wrapper"
      style={{
        width: FRAME_W * finalScale,
        height: FRAME_H * finalScale,
        position: "relative",
        flexShrink: 0,
      }}
    >
      <div
        ref={wrapperRef}
        className="slide-frame slide-container"
        style={{
          width: FRAME_W,
          height: FRAME_H,
          transform: `scale(${finalScale})`,
          transformOrigin: "0 0",
          position: "absolute",
          left: 0,
          top: 0,
          overflow: "hidden",
          borderRadius: 3,
          boxShadow: "0 20px 60px rgba(15,23,42,0.22)",
          flexShrink: 0,
        }}
      >
        {/* Z-0: background */}
        <BackgroundLayer
          background={slide.background}
          backgroundImage={bgImage}
        />

        {/* Z-2: layout content */}
        <ContentLayer slide={slide} />

        {/* Z-4: footer */}
        <FooterLayer slideNumber={slideNumber} totalSlides={totalSlides} />

        {/* Z-5: logo */}
        <LogoLayer />

        {/* Z-10+: optional editing overlay passed as children */}
        {children}
      </div>
    </div>
  );
};
