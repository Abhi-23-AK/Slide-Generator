import React from "react";
import type { Slide } from "../../types";
import { EditableText } from "../EditableText";
import { SlideTheme } from "../../utils/themeUtils";
import SlideHeading from "../../components/SlideHeading";

interface LayoutProps {
  slide: Slide;
  theme: SlideTheme;
}

export const NeuroHeroLayout: React.FC<LayoutProps> = ({ slide, theme }) => {
  const zone = slide.zone_content || {};

  const title = zone.title || slide.title || "Professionals Service.";
  const bullets = zone.bullet_points || [];

  const c1Title = bullets[0] || "Modern Design";
  const c2Title = bullets[1] || "Creative Thinking";

  const imageElement = slide.elements.find((el) => el.kind === "image");
  const imgSource = zone.background_image || imageElement?.text || "";

  // Neumorphic style tokens
  const baseBg = "#F1F4F7";
  const textDark = "#122A6E";
  const textMuted = "#556080";
  const pinkColor = "#FF5AA0";
  const orangeColor = "#FFB43C";
  const blueColor = "#46BEFF";

  const outsetShadow = "9px 9px 16px #CDD2DC, -9px -9px 16px #FFFFFF";
  const insetShadow = "inset 3px 3px 6px #CDD2DC, inset -3px -3px 6px #FFFFFF";

  return (
    <div
      className="neuro-hero-layout"
      style={{
        display: "flex",
        flexDirection: "row",
        width: "100%",
        height: "100%",
        backgroundColor: baseBg,
        fontFamily: "Times New Roman, serif",
        overflow: "hidden",
        position: "relative",
        boxSizing: "border-box",
        padding: "60px 80px",
        alignItems: "center",
      }}
    >
      {/* Left side (Content) */}
      <div
        style={{
          width: "48%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          boxSizing: "border-box",
          zIndex: 2,
        }}
      >
        {/* Title */}
        <div style={{ marginTop: "40px" }}>
          <SlideHeading
            title={title}
            icon_emoji={slide.icon_emoji}
            theme={theme}
            slide={slide}
            zoneKey="title"
            style={{
              justifyContent: "flex-start",
              marginBottom: "20px",
            }}
            textStyle={{
              color: textDark,
              fontSize: "64px",
              fontWeight: "300",
              textAlign: "left",
              lineHeight: 1.1,
              fontFamily: "Times New Roman, serif",
            }}
          />

          {/* Decorative Dots */}
          <div style={{ display: "flex", gap: "12px", marginTop: "24px" }}>
            {[pinkColor, orangeColor, blueColor].map((color, i) => (
              <div
                key={i}
                style={{
                  width: "12px",
                  height: "12px",
                  borderRadius: "50%",
                  backgroundColor: color,
                  boxShadow: "inset 1px 1px 2px rgba(0,0,0,0.1)",
                }}
              />
            ))}
          </div>
        </div>

        {/* Floating Cards row */}
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            gap: "24px",
            marginBottom: "20px",
            width: "100%",
          }}
        >
          {/* Card 1 */}
          <div
            style={{
              flex: 1,
              backgroundColor: baseBg,
              borderRadius: "24px",
              boxShadow: outsetShadow,
              padding: "24px",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
              boxSizing: "border-box",
              border: "1px solid rgba(255,255,255,0.8)",
            }}
          >
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "50%",
                backgroundColor: pinkColor,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#FFFFFF",
                fontSize: "16px",
                boxShadow: insetShadow,
              }}
            >
              ✦
            </div>
            <EditableText
              slide={slide}
              zoneKey="bullet_points.0"
              value={c1Title}
              style={{
                color: textDark,
                fontWeight: "700",
                fontSize: "16px",
                margin: 0,
                textAlign: "left",
                fontFamily: "Times New Roman, serif",
              }}
            />
          </div>

          {/* Card 2 */}
          <div
            style={{
              flex: 1,
              backgroundColor: baseBg,
              borderRadius: "24px",
              boxShadow: outsetShadow,
              padding: "24px",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
              boxSizing: "border-box",
              border: "1px solid rgba(255,255,255,0.8)",
            }}
          >
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "50%",
                backgroundColor: orangeColor,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#FFFFFF",
                fontSize: "16px",
                boxShadow: insetShadow,
              }}
            >
              ✦
            </div>
            <EditableText
              slide={slide}
              zoneKey="bullet_points.1"
              value={c2Title}
              style={{
                color: textDark,
                fontWeight: "700",
                fontSize: "16px",
                margin: 0,
                textAlign: "left",
                fontFamily: "Times New Roman, serif",
              }}
            />
          </div>
        </div>
      </div>

      {/* Right side (Organic Image frame) */}
      <div
        style={{
          width: "52%",
          height: "100%",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          zIndex: 1,
        }}
      >
        <div
          style={{
            width: "520px",
            height: "520px",
            backgroundColor: baseBg,
            boxShadow: outsetShadow,
            borderRadius: "0 50% 50% 50%", // Teardrop organic shape
            overflow: "hidden",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            border: "8px solid #F1F4F7",
          }}
        >
          {imgSource ? (
            <img
              src={imgSource}
              alt="Teardrop representation"
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
              }}
            />
          ) : (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                color: textMuted,
              }}
            >
              <svg
                width="64"
                height="64"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <polyline points="21 15 16 10 5 21" />
              </svg>
              <span style={{ fontSize: "14px", marginTop: "12px" }}>
                Visual Asset Pebble
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
