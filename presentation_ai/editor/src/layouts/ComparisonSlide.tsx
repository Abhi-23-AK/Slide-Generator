import React from "react";
import type { Slide } from "../types";
import { CheckCircle2, XCircle, Trophy } from "lucide-react";
import { SlideTheme } from "../utils/themeUtils";
import { DecorativeElement } from "../components/DecorativeElement";
import SlideHeading from "../components/SlideHeading";

interface LayoutProps {
  slide: Slide;
  theme: SlideTheme;
}

/**
 * ComparisonSlide – Two side-by-side panels with item-by-item comparison rows.
 * Optionally highlights the winning column.
 */
export const ComparisonSlide: React.FC<LayoutProps> = ({ slide, theme }) => {
  const zone = slide.zone_content || {};

  const title = zone.title || slide.title || "Comparison";
  const subtitle = zone.subtitle;
  const highlightSide: "left" | "right" | undefined = zone.highlightSide || zone.highlight_side;

  // --- Structured rows ---
  const defaultRows = [
    { label: "Performance", left: "High throughput", right: "Moderate throughput" },
    { label: "Scalability", left: "Horizontal", right: "Vertical only" },
    { label: "Cost", left: "$$$", right: "$" },
    { label: "Ecosystem", left: "Mature", right: "Growing" },
    { label: "Ease of Use", left: "Moderate", right: "Very Easy" },
  ];

  let rows: { label: string; left: string; right: string }[] = zone.rows || null;

  if (!rows) {
    // Try to synthesise from left/right item lists (structured or flat)
    const leftItems = zone.left?.items || zone.left_points || [];
    const rightItems = zone.right?.items || zone.right_points || [];
    if (leftItems.length && rightItems.length) {
      rows = leftItems.map((l: string, i: number) => ({
        label: `Feature ${i + 1}`,
        left: l,
        right: rightItems[i] || "—",
      }));
    } else if (leftItems.length) {
      rows = leftItems.map((l: string, i: number) => ({
        label: `Feature ${i + 1}`,
        left: l,
        right: "—",
      }));
    } else {
      // Fallback: try extracting from elements
      const listEl = slide.elements.find((el) => el.kind === "icon" || el.kind === "table" || el.kind === "flow");
      if (listEl && listEl.items && listEl.items.length >= 2) {
        rows = listEl.items.map((item, i) => ({
          label: item,
          left: i % 2 === 0 ? "✓ Supported" : "Partial",
          right: i % 2 === 0 ? "Limited" : "✓ Full",
        }));
      } else {
        rows = defaultRows;
      }
    }
  }

  const leftHeading = zone.left?.heading || zone.left_title || "Option A";
  const rightHeading = zone.right?.heading || zone.right_title || "Option B";

  const isTechnical = theme.decorativeShape === "glow";
  const isProfessional = theme.tone === "professional";

  const cardBorder = isProfessional ? "1px solid #E5E7EB" : (isTechnical ? `1px solid ${theme.primary}` : `1px solid ${theme.cardBorder}`);
  const cardShadow = isProfessional ? "none" : (isTechnical ? theme.glowEffect : theme.cardShadow);

  return (
    <div 
      className="layout-container comparison-layout"
      style={{
        backgroundColor: slide.background || theme.slideBackground,
        fontFamily: theme.bodyFont,
        width: '100%', height: '100%',
        position: 'relative',
        boxSizing: 'border-box',
        overflow: 'hidden',
      }}
    >
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
        {subtitle && (
          <p 
            className="layout-subtitle"
            style={{
              color: theme.textMuted,
              fontWeight: '400',
              fontSize: '16px',
              margin: '8px 0 0 0',
            }}
          >
            {subtitle}
          </p>
        )}
      </div>

      <div 
        className="comparison-body"
        style={{
          background: theme.cardBackground,
          border: cardBorder,
          boxShadow: cardShadow,
          borderRadius: '16px',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          height: 'calc(100% - 140px)',
        }}
      >
        {/* Column headers */}
        <div 
          className="comparison-header-row"
          style={{
            display: 'grid',
            gridTemplateColumns: '1.2fr 1fr 1fr',
            background: isTechnical ? 'rgba(0,212,255,0.15)' : theme.primary,
            color: isTechnical ? '#00D4FF' : theme.textOnPrimary,
            fontWeight: 700,
            fontSize: '16px',
            padding: '16px 24px',
            borderBottom: `2px solid ${theme.primary}`,
          }}
        >
          <div className="comparison-label-header">Criteria</div>
          <div className={`comparison-col-header ${highlightSide === "left" ? "highlighted" : ""}`} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {highlightSide === "left" && <Trophy size={16} style={{ color: '#F59E0B' }} />}
            {leftHeading}
          </div>
          <div className={`comparison-col-header ${highlightSide === "right" ? "highlighted" : ""}`} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {highlightSide === "right" && <Trophy size={16} style={{ color: '#F59E0B' }} />}
            {rightHeading}
          </div>
        </div>

        {/* Rows */}
        <div className="comparison-rows" style={{ display: 'flex', flexDirection: 'column', flex: 1, overflowY: 'auto' }}>
          {rows.slice(0, 6).map((row, idx) => {
            const leftWins = highlightSide === "left";
            const rightWins = highlightSide === "right";
            const rowBg = idx % 2 === 0 ? theme.cardBackground : (isProfessional ? "#FFFFFF" : (isTechnical ? 'rgba(255,255,255,0.02)' : theme.secondary));
            return (
              <div 
                className={`comparison-row ${idx % 2 === 0 ? "even" : "odd"}`} 
                key={idx}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1.2fr 1fr 1fr',
                  background: rowBg,
                  padding: '14px 24px',
                  alignItems: 'center',
                  borderBottom: `1px solid ${theme.cardBorder}`,
                }}
              >
                <div className="comparison-row-label" style={{ fontWeight: 600, color: theme.textHeading, fontSize: '15px' }}>{row.label}</div>
                <div className={`comparison-cell ${leftWins ? "winner" : ""}`} style={{ display: 'flex', alignItems: 'center', gap: '8px', color: theme.textBody, fontSize: '14px' }}>
                  {leftWins ? (
                    <CheckCircle2 size={16} style={{ color: '#10B981', flexShrink: 0 }} />
                  ) : (
                    <XCircle size={16} style={{ color: '#EF4444', flexShrink: 0 }} />
                  )}
                  <span style={{ fontWeight: leftWins ? 600 : 400 }}>{row.left}</span>
                </div>
                <div className={`comparison-cell ${rightWins ? "winner" : ""}`} style={{ display: 'flex', alignItems: 'center', gap: '8px', color: theme.textBody, fontSize: '14px' }}>
                  {rightWins ? (
                    <CheckCircle2 size={16} style={{ color: '#10B981', flexShrink: 0 }} />
                  ) : (
                    <XCircle size={16} style={{ color: '#EF4444', flexShrink: 0 }} />
                  )}
                  <span style={{ fontWeight: rightWins ? 600 : 400 }}>{row.right}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
