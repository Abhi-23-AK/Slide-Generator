import React from "react";
import type { Slide } from "../../types";
import { EditableText } from "../EditableText";
import { SlideTheme } from "../../utils/themeUtils";
import SlideHeading from "../../components/SlideHeading";
import { Sparkles } from "lucide-react";

interface LayoutProps {
  slide: Slide;
  theme: SlideTheme;
}

export const NeuroDashboardLayout: React.FC<LayoutProps> = ({ slide, theme }) => {
  const zone = slide.zone_content || {};

  const title = zone.title || slide.title || "Dashboard";

  const defaultStats = [
    { label: "QoQ Revenue", value: "+18.2%" },
    { label: "CAC Index", value: "$125" },
    { label: "LTV Projection", value: "$1,450" },
    { label: "Active Users", value: "24.5K" },
  ];

  let stats = zone.dashboard_metrics || zone.stats || null;
  if (!stats && zone.stat_row) {
    stats = [
      { label: "Overview", value: zone.stat_row },
      { label: "QoQ Revenue", value: "+18.2%" },
      { label: "LTV Projection", value: "$1,450" },
      { label: "Active Users", value: "24.5K" },
    ];
  }
  if (!stats) {
    const listElement = slide.elements.find((el) => el.kind === "icon" || el.kind === "table");
    if (listElement && listElement.items && listElement.items.length >= 2) {
      stats = listElement.items.slice(0, 4).map((item, idx) => {
        const parts = item.split(":");
        return {
          label: parts[0]?.trim?.() || parts[0] || "Metric",
          value: parts[1]?.trim?.() || parts[1] || (idx % 2 === 0 ? "84.5%" : "$12,400"),
        };
      });
    } else {
      stats = defaultStats;
    }
  }

  const finalStats = stats.slice(0, 4);
  while (finalStats.length < 4) {
    finalStats.push(defaultStats[finalStats.length]);
  }

  // Insight text
  const insightText =
    zone.dashboard_insight ||
    zone.insight ||
    zone.body ||
    slide.elements.find((el) => el.kind === "text" && el.id !== "title-1" && el.id !== "abstract-title")?.text ||
    "Strong user retention and pricing optimizations have yielded double-digit revenue expansions across all major product lines this quarter.";

  // Neumorphic style tokens
  const baseBg = "#F1F4F7";
  const textDark = "#122A6E";
  const textMuted = "#556080";
  const pinkColor = "#FF5AA0";
  const orangeColor = "#FFB43C";
  const tealColor = "#28DCB4";
  const blueColor = "#46BEFF";

  const outsetShadow = "9px 9px 16px #CDD2DC, -9px -9px 16px #FFFFFF";
  const insetShadow = "inset 3px 3px 6px #CDD2DC, inset -3px -3px 6px #FFFFFF";

  const statColors = [pinkColor, orangeColor, tealColor, blueColor];

  return (
    <div
      className="neuro-dashboard-layout"
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
          {[pinkColor, orangeColor, tealColor].map((color, i) => (
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

      {/* Main Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.2fr 0.8fr",
          gap: "30px",
          height: "calc(100% - 110px)",
        }}
      >
        {/* Left Card with Scattered / Grid Badges */}
        <div
          style={{
            backgroundColor: baseBg,
            borderRadius: "24px",
            boxShadow: outsetShadow,
            border: "1px solid rgba(255,255,255,0.8)",
            padding: "36px",
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gridTemplateRows: "1fr 1fr",
            gap: "24px",
            alignItems: "center",
            justifyContent: "center",
            boxSizing: "border-box",
            position: "relative",
          }}
        >
          {finalStats.map((stat: any, index: number) => {
            const badgeColor = statColors[index % statColors.length];
            // Scattered-like alignment offsets
            const offsets = [
              { justifySelf: "start", alignSelf: "start", paddingLeft: "20px" },
              { justifySelf: "end", alignSelf: "start", paddingRight: "20px", paddingTop: "20px" },
              { justifySelf: "start", alignSelf: "end", paddingLeft: "40px", paddingBottom: "20px" },
              { justifySelf: "end", alignSelf: "end", paddingRight: "10px" },
            ];

            return (
              <div
                key={index}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: "10px",
                  ...offsets[index],
                }}
              >
                {/* Metric circular badge */}
                <div
                  style={{
                    width: "90px",
                    height: "90px",
                    borderRadius: "50%",
                    backgroundColor: badgeColor,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    boxShadow: insetShadow,
                    color: "#FFFFFF",
                    fontSize: "20px",
                    fontWeight: "bold",
                  }}
                >
                  {stat.value}
                </div>
                {/* Label */}
                <span
                  style={{
                    color: textMuted,
                    fontSize: "12px",
                    fontWeight: "bold",
                    textAlign: "center",
                    fontFamily: "Times New Roman, serif",
                  }}
                >
                  {stat.label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Right Executive Insights Card */}
        <div
          style={{
            backgroundColor: baseBg,
            borderRadius: "24px",
            boxShadow: outsetShadow,
            border: "1px solid rgba(255,255,255,0.8)",
            padding: "30px 24px",
            boxSizing: "border-box",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            height: "100%",
            position: "relative",
          }}
        >
          <div>
            {/* Sparkle badge */}
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "50%",
                backgroundColor: blueColor,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#FFFFFF",
                marginBottom: "16px",
                boxShadow: insetShadow,
              }}
            >
              <Sparkles size={18} />
            </div>

            <h3
              style={{
                color: textDark,
                fontWeight: "700",
                fontSize: "20px",
                margin: "0 0 12px 0",
                fontFamily: "Times New Roman, serif",
              }}
            >
              {zone.insight_title || "Executive Insights"}
            </h3>

            <p
              style={{
                color: textMuted,
                fontSize: "13px",
                lineHeight: 1.6,
                margin: 0,
                fontFamily: "Times New Roman, serif",
              }}
            >
              {insightText}
            </p>
          </div>

          {/* Floating gradient highlight badge */}
          <div
            style={{
              width: "100%",
              padding: "12px",
              borderRadius: "16px",
              backgroundColor: orangeColor,
              color: "#FFFFFF",
              textAlign: "center",
              fontWeight: "bold",
              fontSize: "14px",
              boxShadow: insetShadow,
              boxSizing: "border-box",
              fontFamily: "Times New Roman, serif",
            }}
          >
            {finalStats[0]?.value || "+4.2% Growth Target"}
          </div>
        </div>
      </div>
    </div>
  );
};
