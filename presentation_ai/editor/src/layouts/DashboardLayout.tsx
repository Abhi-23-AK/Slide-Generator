import React from "react";
import type { Slide } from "../types";
import { Sparkles, TrendingUp } from "lucide-react";
import { SlideTheme } from "../utils/themeUtils";
import { DecorativeElement } from "../components/DecorativeElement";
import SlideHeading from "../components/SlideHeading";

interface LayoutProps {
  slide: Slide;
  theme: SlideTheme;
}

export const DashboardLayout: React.FC<LayoutProps> = ({ slide, theme }) => {
  const zone = slide.zone_content || {};

  const defaultStats = [
    { label: "QoQ Revenue", value: "+18.2%" },
    { label: "CAC Index", value: "$125" },
    { label: "LTV Projection", value: "$1,450" },
  ];

  let stats = zone.stats || null;
  if (!stats && zone.stat_row) {
    stats = [
      { label: "Overview", value: zone.stat_row },
      { label: "QoQ Revenue", value: "+18.2%" },
      { label: "LTV Projection", value: "$1,450" }
    ];
  }
  if (!stats) {
    const listElement = slide.elements.find((el) => el.kind === "icon" || el.kind === "table");
    if (listElement && listElement.items && listElement.items.length >= 2) {
      stats = listElement.items.slice(0, 3).map((item, idx) => ({
        label: item,
        value: idx % 2 === 0 ? "84.5%" : "$12,400",
      }));
    } else {
      stats = defaultStats;
    }
  }
  // Make sure we have exactly 3 stats
  const finalStats = stats.slice(0, 3);
  while (finalStats.length < 3) {
    finalStats.push(defaultStats[finalStats.length]);
  }

  // Chart data
  const chartElement = slide.elements.find((el) => el.kind === "chart");
  const chartItems = zone.chart_items || (chartElement ? chartElement.items : null) || ["Speed", "Quality", "Cost"];

  // Insight text
  const insightText =
    zone.insight ||
    zone.insight_area ||
    zone.body ||
    slide.elements.find((el) => el.kind === "text" && el.id !== "title-1" && el.id !== "abstract-title")?.text ||
    "Strong user retention and pricing optimizations have yielded double-digit revenue expansions across all major product lines this quarter.";

  const isTechnical = theme.decorativeShape === "glow";

  const cardBorder = isTechnical ? `1px solid ${theme.primary}` : `1px solid ${theme.cardBorder}`;
  const cardShadow = isTechnical ? theme.glowEffect : theme.cardShadow;

  return (
    <div 
      className="layout-container dashboard-layout"
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
          title={slide.title}
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
          <p 
            className="layout-subtitle"
            style={{
              color: theme.textMuted,
              fontWeight: '400',
              fontSize: '16px',
              margin: '8px 0 0 0',
            }}
          >
            {zone.subtitle}
          </p>
        )}
      </div>

      <div className="dashboard-grid" style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '24px', height: 'calc(100% - 140px)' }}>
        <div className="dashboard-left" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="dashboard-stats-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            {finalStats.map((stat: any, index: number) => (
              <div 
                className="dashboard-stat-mini" 
                key={index}
                style={{
                  background: theme.cardBackground,
                  border: cardBorder,
                  boxShadow: cardShadow,
                  borderRadius: '12px',
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}
              >
                <span className="stat-mini-label" style={{ color: isTechnical ? '#FFFFFF' : theme.textMuted, fontSize: '13px', fontWeight: 600 }}>{stat.label}</span>
                <span className="stat-mini-value" style={{ color: theme.primary, fontSize: '24px', fontWeight: 700 }}>{stat.value}</span>
              </div>
            ))}
          </div>

          <div 
            className="dashboard-chart-area"
            style={{
              background: theme.cardBackground,
              border: cardBorder,
              boxShadow: cardShadow,
              borderRadius: '16px',
              padding: '24px',
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <span style={{ fontSize: "14px", fontWeight: 700, color: theme.textHeading }}>Quarterly Trends Analysis</span>
              <div style={{ display: "flex", gap: "10px", fontSize: "12px", color: theme.textMuted }}>
                <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <span style={{ width: "10px", height: "10px", borderRadius: "50%", background: theme.primary }} />
                  Performance
                </span>
              </div>
            </div>
            
            <div className="chart-bars" style={{ height: "140px", padding: 0, display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around' }}>
              {chartItems.map((item: string, index: number) => (
                <div className="bar-wrap" key={item} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', flex: 1 }}>
                  <div 
                    className="bar" 
                    style={{ 
                      height: `${40 + index * 20}%`, 
                      backgroundColor: theme.chartColors[index % theme.chartColors.length] || theme.primary, 
                      borderRadius: "4px 4px 0 0",
                      width: '60%',
                    }} 
                  />
                  <span style={{ fontSize: "11px", fontWeight: 600, color: theme.textMuted }}>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="dashboard-right">
          <div 
            className="insight-card"
            style={{
              background: isTechnical && theme.gradientCards ? theme.gradientCards[0] : theme.cardBackground,
              border: isTechnical ? 'none' : `1px solid ${theme.cardBorder}`,
              boxShadow: cardShadow,
              borderRadius: '16px',
              padding: '28px 24px',
              height: '100%',
              boxSizing: 'border-box',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div 
                className="insight-icon"
                style={{
                  background: isTechnical ? 'rgba(0,212,255,0.1)' : theme.secondary,
                  color: theme.primary,
                  borderRadius: '50%',
                  width: '48px', height: '48px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  marginBottom: '20px',
                }}
              >
                <Sparkles size={24} />
              </div>
              <h3 
                className="insight-title"
                style={{
                  color: isTechnical ? '#FFFFFF' : theme.textHeading,
                  fontWeight: '700',
                  fontSize: '20px',
                  margin: '0 0 12px 0',
                }}
              >
                {zone.insight_title || "Executive Insights"}
              </h3>
              <p 
                className="insight-text"
                style={{
                  color: isTechnical ? '#E2E8F0' : theme.textBody,
                  fontSize: '14px',
                  lineHeight: 1.6,
                  margin: 0,
                }}
              >
                {insightText}
              </p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", color: isTechnical ? '#00D4FF' : theme.primary, marginTop: "20px", fontWeight: 600 }}>
              <TrendingUp size={14} />
              <span>Target Achieved +4.2%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
