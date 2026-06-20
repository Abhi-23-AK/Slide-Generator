import React from "react";
import type { Slide, SlideElement } from "../types";
import { CheckCircle2, Image as ImageIcon, BarChart3, Trophy } from "lucide-react";
import { EditableText } from "./EditableText";
import { SlideTheme } from "../utils/themeUtils";
import { DecorativeElement } from "../components/DecorativeElement";
import SlideHeading from "../components/SlideHeading";

interface LayoutProps {
  slide: Slide;
  theme: SlideTheme;
}

export const TwoColumnLayout: React.FC<LayoutProps> = ({ slide, theme }) => {
  const zone = slide.zone_content || {};

  // Title
  const title = zone.title || slide.title;

  // Subtitle / Left Headline
  const leftHeadline = zone.left_headline || "Key Points";

  // Left body or description
  const leftText =
    zone.left_text ||
    zone.body ||
    slide.elements.find((el) => el.kind === "text" && el.id !== "title-1" && el.id !== "abstract-title" && el.id !== "abstract-body")?.text ||
    "Extracting key concepts and structure directly from the slide content representation.";

  // Bullets
  const bullets: string[] =
    zone.bullets ||
    (Array.isArray(zone.left_text) ? zone.left_text : null) ||
    slide.elements.find((el) => el.kind === "icon" || el.kind === "flow" || el.kind === "chart" || el.kind === "table")?.items ||
    ["Context and core problems definition", "Synthesized solutions and execution plan", "Key deliverables and outcome metrics"];

  // Right Content (visual)
  const rightElement = slide.elements.find(
    (el) => el.kind === "chart" || el.kind === "image" || el.kind === "table" || el.kind === "icon"
  );

  const rightContent = zone.right_content || rightElement || { kind: "placeholder" };

  const isTechnical = theme.decorativeShape === "glow";
  const isProfessional = theme.tone === "professional";

  const renderRightContent = () => {
    const kind = rightContent.kind;
    const items = rightContent.items || (rightContent as SlideElement).items || [];
    const text = rightContent.text || (rightContent as SlideElement).text || "";

    switch (kind) {
      case "chart":
        return (
          <div className="chart-bars" style={{ height: "100%", width: "100%" }}>
            {items.map((item: string, idx: number) => (
              <div className="bar-wrap" key={item}>
                <div 
                  className="bar" 
                  style={{ 
                    height: `${40 + idx * 20}%`, 
                    backgroundColor: theme.chartColors[idx % theme.chartColors.length] || theme.primary,
                    borderRadius: '4px 4px 0 0'
                  }} 
                />
                <span style={{ fontSize: "12px", fontWeight: 600, color: theme.textBody }}>{item}</span>
              </div>
            ))}
            {items.length === 0 && (
              <div className="chart-bars" style={{ height: "100%", width: "100%" }}>
                {["Q1", "Q2", "Q3"].map((item, idx) => (
                  <div className="bar-wrap" key={item}>
                    <div 
                      className="bar" 
                      style={{ 
                        height: `${45 + idx * 18}%`, 
                        backgroundColor: theme.chartColors[idx % theme.chartColors.length] || theme.primary,
                        borderRadius: '4px 4px 0 0'
                      }} 
                    />
                    <span style={{ fontSize: "12px", fontWeight: 600, color: theme.textBody }}>{item}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      case "image":
        if (text && !text.includes("Image placeholder")) {
          return (
            <img src={text} alt="Visual content" style={{ width: "100%", height: "100%", objectFit: "cover", display: "block", borderRadius: "inherit" }} />
          );
        }
        return (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "8px", color: theme.textMuted }}>
            <ImageIcon size={48} className="two-column-bullet-icon" />
            <span style={{ fontSize: "14px", fontWeight: 600 }}>Visual Illustration</span>
          </div>
        );
      case "table":
        return (
          <table className="mini-table" style={{ borderRadius: "8px", overflow: "hidden", border: `1px solid ${theme.cardBorder}`, width: '100%' }}>
            <tbody>
              {items.map((item: string, index: number) => (
                <tr key={item} style={{ background: index % 2 === 0 ? theme.cardBackground : (isProfessional ? "#FFFFFF" : (isTechnical ? "rgba(255,255,255,0.03)" : theme.secondary)) }}>
                  <td style={{ fontWeight: 700, color: isProfessional ? theme.secondary : theme.primary, padding: '10px' }}>0{index + 1}</td>
                  <td style={{ color: theme.textBody, padding: '10px' }}>{item}</td>
                </tr>
              ))}
              {items.length === 0 && (
                <>
                  <tr style={{ background: theme.cardBackground }}>
                    <td style={{ fontWeight: 700, color: isProfessional ? theme.secondary : theme.primary, padding: '10px' }}>01</td>
                    <td style={{ color: theme.textBody, padding: '10px' }}>Core Metric A</td>
                  </tr>
                  <tr style={{ background: isProfessional ? "#FFFFFF" : (isTechnical ? "rgba(255,255,255,0.03)" : theme.secondary) }}>
                    <td style={{ fontWeight: 700, color: isProfessional ? theme.secondary : theme.primary, padding: '10px' }}>02</td>
                    <td style={{ color: theme.textBody, padding: '10px' }}>Secondary Indicator</td>
                  </tr>
                </>
              )}
            </tbody>
          </table>
        );
      case "architecture":
      case "flowchart": {
        const labels = items.length >= 2 ? items : ["Service", "Data", "Security"];
        const nodes = [
          { id: "1", label: "Client", x: 90, y: 15, type: "gateway" },
          { id: "2", label: labels[0] || "API Gateway", x: 15, y: 100, type: "service" },
          { id: "3", label: labels[1] || "App Service", x: 165, y: 100, type: "service" },
          { id: "4", label: labels[2] || "Database", x: 90, y: 185, type: "database" },
        ];
        const connections = [
          { from: "1", to: "2" },
          { from: "1", to: "3" },
          { from: "2", to: "4" },
          { from: "3", to: "4" },
        ];
        const nodeMap = new Map<string, any>(nodes.map((n) => [n.id, n]));
        return (
          <div className="diagram-canvas" style={{ width: "100%", height: "100%", minHeight: "260px", background: "transparent", border: "none", boxShadow: "none", position: "relative", overflow: "hidden" }}>
            <svg className="diagram-svg-overlay" style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", pointerEvents: "none" }}>
              <defs>
                <marker id="mini-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
                  <path d="M 0 2 L 10 5 L 0 8 z" fill={theme.textMuted} />
                </marker>
              </defs>
              {connections.map((conn: any, idx: number) => {
                const fromNode = nodeMap.get(conn.from);
                const toNode = nodeMap.get(conn.to);
                if (!fromNode || !toNode) return null;

                const startX = fromNode.x + 55;
                const startY = fromNode.y + 20;
                const endX = toNode.x + 55;
                const endY = toNode.y + 20;

                return (
                  <path
                    key={idx}
                    d={`M ${startX} ${startY} L ${endX} ${endY}`}
                    fill="none"
                    stroke={theme.textMuted}
                    strokeWidth="1.5"
                    markerEnd="url(#mini-arrow)"
                    opacity="0.6"
                  />
                );
              })}
            </svg>
            {nodes.map((node) => (
              <div
                key={node.id}
                className={`diagram-node ${node.type}`}
                style={{
                  position: "absolute",
                  left: `${node.x}px`,
                  top: `${node.y}px`,
                  padding: "6px 10px",
                  fontSize: "12px",
                  fontWeight: 700,
                  minWidth: "110px",
                  textAlign: "center",
                  borderRadius: "6px",
                  border: `1.5px solid ${theme.primary}`,
                  background: theme.cardBackground,
                  color: theme.textHeading,
                  boxShadow: theme.glowEffect || theme.cardShadow,
                  transform: "none",
                  height: "38px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{node.label}</span>
              </div>
            ))}
          </div>
        );
      }
      case "process":
      case "mindmap": {
        const steps = items.length > 0 ? items : ["Phase 1", "Phase 2", "Phase 3"];
        return (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", width: "100%", height: "100%", padding: "10px" }}>
            {steps.slice(0, 3).map((step: string, idx: number) => {
              const isLast = idx === Math.min(steps.length, 3) - 1;
              return (
                <React.Fragment key={idx}>
                  <div style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: "8px",
                    background: theme.cardBackground,
                    border: `1px solid ${theme.cardBorder}`,
                    borderRadius: "8px",
                    padding: "12px 10px",
                    flex: 1,
                    textAlign: "center",
                    minWidth: "70px",
                    boxShadow: theme.glowEffect || theme.cardShadow,
                  }}>
                    <span style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      width: "32px",
                      height: "32px",
                      borderRadius: "50%",
                      background: theme.primary,
                      color: theme.textOnPrimary,
                      fontSize: "13px",
                      fontWeight: 800,
                    }}>
                      {idx + 1}
                    </span>
                    <span style={{ fontSize: "12px", fontWeight: 700, color: theme.textHeading, wordBreak: "break-word" }}>{step}</span>
                  </div>
                  {!isLast && (
                    <div style={{ width: "20px", height: "2px", background: theme.primary, flexShrink: 0 }} />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        );
      }
      case "comparison": {
        const leftLabel = items[0] || "Option A";
        const rightLabel = items[1] || "Option B";
        return (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", width: "100%", height: "100%", padding: "10px" }}>
            <div style={{ background: theme.cardBackground, border: `1px solid ${theme.cardBorder}`, borderRadius: "8px", padding: "16px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "8px", boxShadow: theme.glowEffect || theme.cardShadow }}>
              <span style={{ fontSize: "16px", fontWeight: 800, color: theme.primary }}>{leftLabel}</span>
              <span style={{ fontSize: "12px", color: theme.textMuted }}>Primary Option</span>
            </div>
            <div style={{ background: theme.cardBackground, border: `1px solid ${theme.cardBorder}`, borderRadius: "8px", padding: "16px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "8px", boxShadow: theme.glowEffect || theme.cardShadow }}>
              <span style={{ fontSize: "16px", fontWeight: 800, color: theme.secondary }}>{rightLabel}</span>
              <span style={{ fontSize: "12px", color: theme.textMuted }}>Alternative</span>
            </div>
          </div>
        );
      }
      case "icon":
      default:
        if (items.length > 0) {
          return (
            <div className="icon-grid" style={{ padding: "10px", width: "100%", height: "100%" }}>
              {items.map((item: string) => (
                <div className="icon-chip" key={item} style={{ background: theme.cardBackground, color: theme.textHeading, border: `1px solid ${theme.cardBorder}`, borderRadius: "6px", display: "flex", alignItems: "center", gap: "8px", padding: "8px 12px", boxShadow: theme.glowEffect || theme.cardShadow }}>
                  <CheckCircle2 size={16} style={{ color: theme.primary, flexShrink: 0 }} />
                  <span style={{ fontWeight: 600, fontSize: "13px" }}>{item}</span>
                </div>
              ))}
            </div>
          );
        }
        return (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "10px", color: theme.textMuted }}>
            <BarChart3 size={40} />
            <span style={{ fontSize: "13px", fontWeight: 500 }}>No visual element detected</span>
          </div>
        );
    }
  };

  const hasImage = rightContent.kind === "image" && rightContent.text && !rightContent.text.includes("Image placeholder");

  const leftCardStyle: React.CSSProperties = isProfessional ? {
    background: theme.primary,
    border: `1px solid ${theme.primary}`,
    boxShadow: "none",
    color: theme.secondary,
    borderRadius: theme.radiusCard,
    padding: '24px',
  } : (isTechnical ? {
    background: theme.cardBackground,
    boxShadow: theme.glowEffect,
    border: `1px solid ${theme.primary}`,
    color: '#FFFFFF',
    borderRadius: '16px',
    padding: '24px',
  } : {
    background: theme.cardBackground,
    border: `1px solid ${theme.cardBorder}`,
    boxShadow: theme.cardShadow,
    color: theme.textBody,
    borderRadius: '16px',
    padding: '24px',
  });
 
  const rightContainerStyle: React.CSSProperties = isProfessional ? {
    minHeight: "300px",
    borderRadius: theme.radiusCard,
    overflow: "hidden",
    backgroundColor: theme.cardBackground,
    border: `1px solid ${theme.cardBorder}`,
    boxShadow: "none",
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  } : (isTechnical && hasImage ? {
    minHeight: "300px",
    borderRadius: "16px",
    overflow: "hidden",
    boxShadow: theme.glowEffect,
    border: `2px solid ${theme.primary}`
  } : {
    minHeight: "300px",
    borderRadius: "16px",
    overflow: "hidden",
    backgroundColor: theme.cardBackground,
    border: `1px solid ${theme.cardBorder}`,
    boxShadow: theme.glowEffect || theme.cardShadow,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  });

  return (
    <div 
      className="layout-container two-column-layout"
      style={{
        backgroundColor: slide.background || theme.slideBackground,
        fontFamily: theme.bodyFont,
        width: '100%', height: '100%',
        position: 'relative',
        boxSizing: 'border-box',
        overflow: 'hidden',
      }}
    >
      {/* Decorative background hexagon / shape */}
      <DecorativeElement theme={theme} position={{ top: '40px', right: '60px' }} />

      <div className="layout-header" style={{ marginBottom: '24px' }}>
        <SlideHeading
          title={title}
          icon_emoji={slide.icon_emoji}
          theme={theme}
          slide={slide}
          zoneKey="title"
          style={{ marginBottom: 0 }}
        />
        <div style={{
          width: '60px', height: '4px',
          backgroundColor: theme.primary,
          borderRadius: '2px',
          marginTop: '12px',
          marginBottom: '16px'
        }} />
        {zone.subtitle && (
          <EditableText 
            slide={slide} 
            zoneKey="subtitle" 
            value={zone.subtitle} 
            className="layout-subtitle" 
            as="p" 
            style={{
              color: theme.textMuted,
              fontWeight: '400',
              fontSize: '16px',
              margin: '8px 0 0 0',
            }}
          />
        )}
      </div>

      <div className="two-column-body" style={{ display: 'grid', gridTemplateColumns: '1.1fr 0.9fr', gap: '24px', height: 'calc(100% - 140px)' }}>
        <div className="two-column-left-card" style={leftCardStyle}>
          <div className="text-xl font-semibold mb-3" style={{ color: isProfessional ? theme.secondary : (isTechnical ? '#FFFFFF' : theme.textHeading), marginBottom: '12px' }}>
            <EditableText 
              slide={slide} 
              zoneKey="left_headline" 
              value={leftHeadline} 
              as="h2" 
              style={{
                color: isProfessional ? theme.secondary : (isTechnical ? '#FFFFFF' : theme.textHeading),
                fontWeight: '600',
                fontSize: '20px',
                margin: 0,
              }}
            />
          </div>
          {leftText && (
            <div className="text-[28px] font-normal leading-[1.4] mb-5" style={{ color: isProfessional ? theme.secondary : (isTechnical ? '#E2E8F0' : theme.textBody), fontSize: '15px', lineHeight: 1.5, marginBottom: '20px' }}>
              <EditableText slide={slide} zoneKey="left_text" value={leftText} as="p" style={{ margin: 0 }} />
            </div>
          )}
          <div className="two-column-bullets flex flex-col gap-3" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {bullets.map((bullet, index) => {
              let cleaned = bullet.trim();
              for (const prefix of ["•", "-", "*", "✓"]) {
                if (cleaned.startsWith(prefix)) {
                  cleaned = cleaned.substring(prefix.length).trim();
                }
              }
              const isChallenge = cleaned.toLowerCase().startsWith("challenge:") || cleaned.toLowerCase().startsWith("key challenge:") || cleaned.toLowerCase().startsWith("problem:");
              
              if (isProfessional) {
                return (
                  <div 
                    className="flex items-start gap-3 text-base font-normal" 
                    style={{ 
                      color: theme.secondary,
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px',
                      fontSize: '14px',
                      lineHeight: 1.4,
                    }} 
                    key={index}
                  >
                    <span style={{ color: theme.secondary, fontSize: '18px', fontWeight: 'bold', lineHeight: 1 }}>✓</span>
                    <EditableText slide={slide} zoneKey={`bullets.${index}`} value={cleaned} as="span" style={{ flex: 1 }} />
                  </div>
                );
              }

              if (isChallenge) {
                const colonIdx = bullet.indexOf(":");
                const label = colonIdx !== -1 ? bullet.substring(0, colonIdx + 1) : "Challenge:";
                const body = colonIdx !== -1 ? bullet.substring(colonIdx + 1) : bullet;
                return (
                  <div 
                    key={index} 
                    style={{ 
                      background: isTechnical ? '#1E293B' : '#DCFCE7', 
                      borderLeft: `4px solid ${theme.primary}`, 
                      borderRadius: "8px", 
                      padding: "12px 16px", 
                      display: "flex", 
                      gap: "12px", 
                      alignItems: "flex-start", 
                      marginTop: "4px" 
                    }}
                  >
                    <span style={{ color: theme.bulletColor, fontSize: '18px', lineHeight: 1 }}>●</span>
                    <div style={{ fontSize: "15px", color: isTechnical ? '#FFFFFF' : theme.textHeading, flex: 1, display: "flex", flexDirection: "row", flexWrap: "wrap", gap: "4px" }}>
                      <span style={{ fontWeight: 700 }}>{label}</span>
                      <EditableText slide={slide} zoneKey={`bullets.${index}`} value={body.trim()} as="span" style={{ fontWeight: 400, color: isTechnical ? '#E2E8F0' : theme.textBody }} />
                    </div>
                  </div>
                );
              }
              return (
                <div 
                  className="flex items-start gap-3 text-base font-normal" 
                  style={{ 
                    color: isTechnical ? '#E2E8F0' : theme.textBody,
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px'
                  }} 
                  key={index}
                >
                  <span style={{ color: theme.bulletColor, fontSize: '18px', lineHeight: 1 }}>●</span>
                  <EditableText slide={slide} zoneKey={`bullets.${index}`} value={bullet} as="span" style={{ flex: 1 }} />
                </div>
              );
            })}
          </div>
        </div>

        <div 
          className={`two-column-right ${hasImage ? "is-image" : ""}`} 
          style={rightContainerStyle}
        >
          {renderRightContent()}
        </div>
      </div>
    </div>
  );
};
