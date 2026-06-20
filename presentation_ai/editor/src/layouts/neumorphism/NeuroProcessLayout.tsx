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

export const NeuroProcessLayout: React.FC<LayoutProps> = ({ slide, theme }) => {
  const zone = slide.zone_content || {};

  const title = zone.title || slide.title || "Workflow";
  const subtitle = zone.subtitle;

  const defaultSteps = [
    { title: "Research", body: "Gather requirements, analyze existing data, and identify constraints." },
    { title: "Design", body: "Create wireframes, define architecture, and establish design tokens." },
    { title: "Build", body: "Implement core modules, integrate APIs, and write unit tests." },
    { title: "Test", body: "Run QA cycles, performance benchmarks, and user acceptance testing." },
  ];

  let steps = zone.process_steps || zone.steps || null;
  if (Array.isArray(steps) && steps.length > 0 && typeof steps[0] === "string") {
    steps = (steps as string[]).map((item: string) => {
      const parsed = parseBulletPoint(item);
      return {
        title: parsed.title,
        body: parsed.description,
      };
    });
  }

  if (!steps) {
    const listEl = slide.elements.find(
      (el) => el.kind === "flow" || el.kind === "icon" || el.kind === "table"
    );
    if (listEl && listEl.items && listEl.items.length >= 2) {
      steps = listEl.items.map((item) => {
        const parsed = parseBulletPoint(item);
        return {
          title: parsed.title,
          body: parsed.description,
        };
      });
    } else {
      steps = defaultSteps;
    }
  }

  const finalSteps = steps.slice(0, 4);
  while (finalSteps.length < 4) {
    finalSteps.push(defaultSteps[finalSteps.length]);
  }

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

  const stepColors = [pinkColor, orangeColor, tealColor, blueColor];
  
  // Custom rotation style matching python pptx rotations
  const stepShapes = [
    { borderRadius: "0 50% 50% 50%", transform: "rotate(45deg)", labelTransform: "rotate(-45deg)" }, // teardrop down-right
    { borderRadius: "0 50% 50% 50%", transform: "rotate(-45deg)", labelTransform: "rotate(45deg)" }, // teardrop up
    { borderRadius: "0 50% 50% 50%", transform: "rotate(135deg)", labelTransform: "rotate(-135deg)" }, // teardrop down-left
    { borderRadius: "50%", transform: "rotate(0deg)", labelTransform: "rotate(0deg)" }, // circle
  ];

  // Heights/offsets to simulate a wavy connection path
  const verticalOffsets = [0, 80, 90, 10];

  return (
    <div
      className="neuro-process-layout"
      style={{
        backgroundColor: baseBg,
        fontFamily: "Times New Roman, serif",
        width: "100%",
        height: "100%",
        position: "relative",
        boxSizing: "border-box",
        padding: "50px 60px",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Header */}
      <div className="layout-header" style={{ marginBottom: "20px", display: "flex", flexDirection: "column", alignItems: "center" }}>
        <SlideHeading
          title={title}
          icon_emoji={slide.icon_emoji}
          theme={theme}
          slide={slide}
          zoneKey="title"
          style={{ marginBottom: 0, justifyContent: "center" }}
          textStyle={{
            color: textDark,
            fontSize: "42px",
            fontWeight: "300",
            fontFamily: "Times New Roman, serif",
            textAlign: "center",
          }}
        />
        {/* Decorative Dots */}
        <div style={{ display: "flex", gap: "8px", marginTop: "12px", justifyContent: "center" }}>
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

      {/* Steps Container */}
      <div
        style={{
          display: "flex",
          flexDirection: "row",
          width: "100%",
          height: "calc(100% - 130px)",
          alignItems: "flex-start",
          justifyContent: "space-between",
          boxSizing: "border-box",
          padding: "20px 40px 0 40px",
          position: "relative",
        }}
      >
        {/* SVG curved path connecting elements */}
        <svg
          style={{
            position: "absolute",
            top: "90px",
            left: "140px",
            width: "calc(100% - 280px)",
            height: "180px",
            zIndex: 1,
            pointerEvents: "none",
          }}
          viewBox="0 0 800 200"
          fill="none"
        >
          <path
            d="M 10 30 Q 130 150 250 110 T 500 120 T 790 30"
            stroke={textDark}
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray="6 6"
            opacity={0.6}
          />
        </svg>

        {finalSteps.map((step: any, idx: number) => {
          const shapeStyle = stepShapes[idx];
          const color = stepColors[idx];
          const topOffset = verticalOffsets[idx];

          return (
            <div
              key={idx}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                width: "200px",
                position: "relative",
                top: `${topOffset}px`,
                zIndex: 2,
              }}
            >
              {/* Organic Pebble / Teardrop shape */}
              <div
                style={{
                  width: "100px",
                  height: "100px",
                  backgroundColor: baseBg,
                  boxShadow: outsetShadow,
                  borderRadius: shapeStyle.borderRadius,
                  transform: shapeStyle.transform,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  marginBottom: "20px",
                  border: "4px solid #F1F4F7",
                }}
              >
                {/* Number inside badge */}
                <div
                  style={{
                    width: "48px",
                    height: "48px",
                    borderRadius: "50%",
                    backgroundColor: color,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#FFFFFF",
                    fontSize: "20px",
                    fontWeight: "bold",
                    transform: shapeStyle.labelTransform,
                    boxShadow: insetShadow,
                  }}
                >
                  {idx + 1}
                </div>
              </div>

              {/* Title & Description */}
              <h3
                style={{
                  color: textDark,
                  fontSize: "16px",
                  fontWeight: "bold",
                  margin: "0 0 6px 0",
                  textAlign: "center",
                  fontFamily: "Times New Roman, serif",
                }}
              >
                {step.title}
              </h3>
              <p
                style={{
                  color: textMuted,
                  fontSize: "12px",
                  lineHeight: 1.4,
                  margin: 0,
                  textAlign: "center",
                  fontFamily: "Times New Roman, serif",
                }}
              >
                {step.body}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
