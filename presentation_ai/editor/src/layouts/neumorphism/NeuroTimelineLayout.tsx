import React from "react";
import type { Slide } from "../../types";
import { EditableText } from "../EditableText";
import { parseBulletPoint } from "../../types";
import { SlideTheme } from "../../utils/themeUtils";
import SlideHeading from "../../components/SlideHeading";

interface LayoutProps {
  slide: Slide;
  theme: SlideTheme;
}

export const NeuroTimelineLayout: React.FC<LayoutProps> = ({ slide, theme }) => {
  const zone = slide.zone_content || {};

  const title = zone.title || slide.title || "Timeline";

  const defaultEvents = [
    { date: "1", title: "Discovery Phase", description: "Establish core parameters and target personas." },
    { date: "2", title: "Prototyping", description: "Build working mockups for focus feedback." },
    { date: "3", title: "Beta Launch & Release", description: "Open sandbox preview to early access users." },
  ];

  let events = zone.timeline_steps || zone.events || null;
  if (typeof events === "string") {
    events = events.split("\n").filter(Boolean).map((evt: string, idx: number) => {
      const parsed = parseBulletPoint(evt, String(idx + 1));
      return {
        date: parsed.date,
        title: parsed.title,
        description: parsed.description,
      };
    });
  }
  if (!events) {
    const listElement = slide.elements.find((el) => el.kind === "flow" || el.kind === "icon");
    if (listElement && listElement.items && listElement.items.length >= 2) {
      events = listElement.items.map((item, idx) => {
        const parsed = parseBulletPoint(item, String(idx + 1));
        return {
          date: parsed.date,
          title: parsed.title,
          description: parsed.description,
        };
      });
    } else {
      events = defaultEvents;
    }
  }

  const finalEvents = events.slice(0, 3);
  while (finalEvents.length < 3) {
    finalEvents.push(defaultEvents[finalEvents.length]);
  }

  const imageElement = slide.elements.find((el) => el.kind === "image");
  const imgSource = zone.background_image || imageElement?.text || "";

  // Neumorphic style tokens
  const baseBg = "#F1F4F7";
  const textDark = "#122A6E";
  const textMuted = "#556080";
  const pinkColor = "#FF5AA0";
  const orangeColor = "#FFB43C";
  const tealColor = "#28DCB4";

  const outsetShadow = "9px 9px 16px #CDD2DC, -9px -9px 16px #FFFFFF";
  const insetShadow = "inset 3px 3px 6px #CDD2DC, inset -3px -3px 6px #FFFFFF";

  const badgeColors = [pinkColor, orangeColor, tealColor];

  return (
    <div
      className="neuro-timeline-layout"
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
          gridTemplateColumns: "0.85fr 1.15fr",
          gap: "36px",
          height: "calc(100% - 110px)",
          alignItems: "center",
        }}
      >
        {/* Left column: Organic Teardrop Image pebble */}
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
                alt="Timeline representation"
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
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                <span style={{ fontSize: "13px", marginTop: "12px" }}>
                  Timeline Pebble
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Right column: Vertical stacked cards */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "24px",
            justifyContent: "center",
            height: "100%",
          }}
        >
          {finalEvents.map((evt: any, index: number) => {
            const badgeColor = badgeColors[index % badgeColors.length];

            return (
              <div
                key={index}
                style={{
                  backgroundColor: baseBg,
                  borderRadius: "24px",
                  boxShadow: outsetShadow,
                  border: "1px solid rgba(255,255,255,0.8)",
                  padding: "20px 24px",
                  display: "flex",
                  flexDirection: "row",
                  alignItems: "center",
                  gap: "20px",
                  boxSizing: "border-box",
                }}
              >
                {/* Colored circle badge on the left side of the card */}
                <div
                  style={{
                    width: "50px",
                    height: "50px",
                    borderRadius: "50%",
                    backgroundColor: badgeColor,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#FFFFFF",
                    fontSize: "18px",
                    fontWeight: "bold",
                    flexShrink: 0,
                    boxShadow: insetShadow,
                  }}
                >
                  {evt.date || index + 1}
                </div>

                {/* Text content on the right side of the card */}
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <h3
                    style={{
                      color: textDark,
                      fontSize: "16px",
                      fontWeight: "bold",
                      margin: 0,
                      textAlign: "left",
                      fontFamily: "Times New Roman, serif",
                    }}
                  >
                    {evt.title}
                  </h3>
                  <p
                    style={{
                      color: textMuted,
                      fontSize: "12px",
                      margin: 0,
                      lineHeight: 1.4,
                      textAlign: "left",
                      fontFamily: "Times New Roman, serif",
                    }}
                  >
                    {evt.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
