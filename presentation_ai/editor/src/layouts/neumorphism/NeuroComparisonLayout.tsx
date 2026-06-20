import React from "react";
import type { Slide } from "../../types";
import { SlideTheme } from "../../utils/themeUtils";
import SlideHeading from "../../components/SlideHeading";

interface LayoutProps {
  slide: Slide;
  theme: SlideTheme;
}

export const NeuroComparisonLayout: React.FC<LayoutProps> = ({ slide, theme }) => {
  const zone = slide.zone_content || {};

  const title = zone.title || slide.title || "Comparison";

  const defaultLeftPoints = [
    "High performance and throughput",
    "Horizontal scalable clustering",
    "Mature community support",
  ];

  const defaultRightPoints = [
    "Moderate performance",
    "Vertical scaling limits",
    "Growing ecosystem ecosystem",
  ];

  const comparisonItems = zone.comparison_items || [];
  let leftPoints: string[] = [];
  let rightPoints: string[] = [];

  if (comparisonItems.length > 0) {
    leftPoints = comparisonItems.map((item: any) => item.left || "");
    rightPoints = comparisonItems.map((item: any) => item.right || "");
  } else {
    const bullets = zone.bullet_points || [];
    if (bullets.length > 0) {
      const half = Math.max(1, Math.ceil(bullets.length / 2));
      leftPoints = bullets.slice(0, half);
      rightPoints = bullets.slice(half);
    } else {
      leftPoints = defaultLeftPoints;
      rightPoints = defaultRightPoints;
    }
  }

  const imageElement = slide.elements.find((el) => el.kind === "image");
  const imgSource = zone.background_image || imageElement?.text || "";

  // Neumorphic style tokens
  const baseBg = "#F1F4F7";
  const textDark = "#122A6E";
  const textMuted = "#556080";
  const pinkColor = "#FF5AA0";
  const orangeColor = "#FFB43C";

  const outsetShadow = "9px 9px 16px #CDD2DC, -9px -9px 16px #FFFFFF";
  const insetShadow = "inset 3px 3px 6px #CDD2DC, inset -3px -3px 6px #FFFFFF";

  return (
    <div
      className="neuro-comparison-layout"
      style={{
        backgroundColor: baseBg,
        fontFamily: "Times New Roman, serif",
        width: "100%",
        height: "100%",
        position: "relative",
        boxSizing: "border-box",
        padding: "50px 70px",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Header */}
      <div className="layout-header" style={{ marginBottom: "20px" }}>
        <SlideHeading
          title={title}
          icon_emoji={slide.icon_emoji}
          theme={theme}
          slide={slide}
          zoneKey="title"
          style={{ marginBottom: 0 }}
          textStyle={{
            color: textDark,
            fontSize: "48px",
            fontWeight: "300",
            fontFamily: "Times New Roman, serif",
          }}
        />
        {/* Decorative Dots */}
        <div style={{ display: "flex", gap: "8px", marginTop: "12px" }}>
          {[pinkColor, orangeColor].map((color, i) => (
            <div
              key={i}
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: color,
              }}
            />
          ))}
        </div>
      </div>

      {/* Main Content Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.1fr 0.9fr",
          gap: "36px",
          height: "calc(100% - 110px)",
          alignItems: "center",
        }}
      >
        {/* Left column: Stacked Offset Cards */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "24px",
            width: "100%",
            position: "relative",
          }}
        >
          {/* Top Card (Option A) - aligned slightly left */}
          <div
            style={{
              backgroundColor: baseBg,
              borderRadius: "24px",
              boxShadow: outsetShadow,
              border: "1px solid rgba(255,255,255,0.8)",
              padding: "24px 28px",
              width: "90%",
              alignSelf: "flex-start",
              boxSizing: "border-box",
            }}
          >
            <h4
              style={{
                color: textDark,
                fontWeight: "bold",
                fontSize: "16px",
                margin: "0 0 12px 0",
                fontFamily: "Times New Roman, serif",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <span style={{ color: pinkColor }}>✦</span>
              {zone.left_title || "Option A"}
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {leftPoints.map((pt, idx) => (
                <div
                  key={idx}
                  style={{
                    color: textMuted,
                    fontSize: "13px",
                    lineHeight: 1.4,
                    fontFamily: "Times New Roman, serif",
                    textAlign: "left",
                  }}
                >
                  • {pt}
                </div>
              ))}
            </div>
          </div>

          {/* Bottom Card (Option B) - aligned slightly right */}
          <div
            style={{
              backgroundColor: baseBg,
              borderRadius: "24px",
              boxShadow: outsetShadow,
              border: "1px solid rgba(255,255,255,0.8)",
              padding: "24px 28px",
              width: "90%",
              alignSelf: "flex-end",
              boxSizing: "border-box",
            }}
          >
            <h4
              style={{
                color: textDark,
                fontWeight: "bold",
                fontSize: "16px",
                margin: "0 0 12px 0",
                fontFamily: "Times New Roman, serif",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <span style={{ color: orangeColor }}>✦</span>
              {zone.right_title || "Option B"}
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {rightPoints.map((pt, idx) => (
                <div
                  key={idx}
                  style={{
                    color: textMuted,
                    fontSize: "13px",
                    lineHeight: 1.4,
                    fontFamily: "Times New Roman, serif",
                    textAlign: "left",
                  }}
                >
                  • {pt}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right column: Organic Teardrop Image */}
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <div
            style={{
              width: "440px",
              height: "440px",
              backgroundColor: baseBg,
              boxShadow: outsetShadow,
              borderRadius: "0 50% 50% 50%", // Teardrop shape pointing down-right
              overflow: "hidden",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              border: "6px solid #F1F4F7",
            }}
          >
            {imgSource ? (
              <img
                src={imgSource}
                alt="Comparison representation"
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
                  width="56"
                  height="56"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="18" y1="20" x2="18" y2="10" />
                  <line x1="12" y1="20" x2="12" y2="4" />
                  <line x1="6" y1="20" x2="6" y2="14" />
                </svg>
                <span style={{ fontSize: "13px", marginTop: "12px" }}>
                  Visual Asset Pebble
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
