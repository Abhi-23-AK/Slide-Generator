import React from "react";
import type { Slide } from "../types";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { parseMetricBullet } from "../types";
import { EditableText } from "./EditableText";
import { SlideTheme } from "../utils/themeUtils";
import { DecorativeElement } from "../components/DecorativeElement";
import SlideHeading from "../components/SlideHeading";

interface LayoutProps {
  slide: Slide;
  theme: SlideTheme;
}

export const FourGridLayout: React.FC<LayoutProps> = ({ slide, theme }) => {
  const zone = slide.zone_content || {};

  const defaultCards = [
    { label: "Active Users", value: "14,250", change: "+12.4%", trend: "up" },
    { label: "Total Revenue", value: "$48,920", change: "+8.2%", trend: "up" },
    { label: "Bounce Rate", value: "32.1%", change: "-4.6%", trend: "down" },
    { label: "Customer Sat", value: "98.2%", change: "+2.1%", trend: "up" },
  ];

  let cards = zone.cards || null;
  if (!cards && (zone.cell_tl || zone.cell_tr || zone.cell_bl || zone.cell_br)) {
    cards = [
      parseMetricBullet(zone.cell_tl || "", 0),
      parseMetricBullet(zone.cell_tr || "", 1),
      parseMetricBullet(zone.cell_bl || "", 2),
      parseMetricBullet(zone.cell_br || "", 3),
    ];
  }
  if (!cards) {
    const listElement = slide.elements.find((el) => el.kind === "chart" || el.kind === "table" || el.kind === "icon");
    if (listElement && listElement.items && listElement.items.length >= 2) {
      cards = listElement.items.map((item, idx) => parseMetricBullet(item, idx));
    } else {
      cards = defaultCards;
    }
  }

  // Ensure we have exactly 4 cards
  const finalCards = cards.slice(0, 4);
  while (finalCards.length < 4) {
    finalCards.push(defaultCards[finalCards.length]);
  }
  const cellKeys = ["cell_tl", "cell_tr", "cell_bl", "cell_br"];

  const isTechnical = theme.decorativeShape === "glow";

  if (theme.tone === "professional") {
    return (
      <div 
        className="layout-container four-grid-layout professional-four-grid"
        style={{
          backgroundColor: slide.background || '#FFFFFF',
          fontFamily: theme.bodyFont,
          width: '100%', height: '100%',
          position: 'relative',
          boxSizing: 'border-box',
          overflow: 'hidden',
          padding: '40px 60px',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header centered */}
        <div className="layout-header" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', marginBottom: '24px' }}>
          <SlideHeading
            title={slide.title}
            icon_emoji={slide.icon_emoji}
            theme={theme}
            slide={slide}
            zoneKey="title"
            style={{ marginBottom: 0, justifyContent: 'center' }}
            textStyle={{
              color: '#141414',
              fontSize: '32px',
              fontWeight: '800',
              fontFamily: theme.headingFont,
              textTransform: 'uppercase',
            }}
          />
          <div style={{
            width: '60px', height: '4px',
            backgroundColor: '#FFD600',
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
                color: '#646464',
                fontWeight: '400',
                fontSize: '16px',
                margin: 0,
              }}
            />
          )}
        </div>

        {/* 2x2 Grid */}
        <div className="four-grid-container" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', flex: 1 }}>
          {finalCards.map((card: any, index: number) => {
            const desc = card.value && card.value !== "0" && isNaN(Number(card.value.replace(/[^0-9.-]+/g,""))) 
              ? card.value 
              : (card.value ? `${card.value} ${card.change || ""}` : (card.desc || ""));
            
            return (
              <div 
                className="metric-card" 
                key={index}
                style={{
                  background: '#F5F5F5',
                  border: '1px solid #E5E7EB',
                  borderRadius: '8px',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'row',
                  gap: '16px',
                  alignItems: 'flex-start',
                  height: '100%',
                  boxSizing: 'border-box',
                }}
              >
                {/* Yellow Badge */}
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  backgroundColor: '#FFD600',
                  color: '#141414',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: '800',
                  fontSize: '12px',
                  flexShrink: 0,
                }}>
                  0{index + 1}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1, textAlign: 'left' }}>
                  <EditableText 
                    slide={slide} 
                    zoneKey={cellKeys[index]} 
                    value={card.label} 
                    className="metric-label" 
                    as="span" 
                    style={{
                      color: '#141414',
                      fontWeight: 700,
                      fontSize: '16px',
                    }}
                  />
                  <EditableText 
                    slide={slide} 
                    zoneKey={cellKeys[index]} 
                    value={desc || "Core focus area metric or description details."} 
                    className="metric-value" 
                    as="p" 
                    style={{
                      color: '#646464',
                      fontWeight: 400,
                      fontSize: '13px',
                      margin: 0,
                      lineHeight: 1.4,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div 
      className="layout-container four-grid-layout"
      style={{
        backgroundColor: slide.background || theme.slideBackground,
        fontFamily: theme.bodyFont,
        width: '100%', height: '100%',
        position: 'relative',
        boxSizing: 'border-box',
        overflow: 'hidden',
      }}
    >
      {/* Decorative element background */}
      <DecorativeElement theme={theme} position={{ top: '50px', right: '60px' }} />

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

      <div className="four-grid-container" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gridTemplateRows: '1fr 1fr', gap: '20px', height: 'calc(100% - 140px)' }}>
        {finalCards.map((card: any, index: number) => {
          const isUp = card.trend === "up" || (card.change && card.change.startsWith("+"));
          const cardBg = theme.cardBackground;
          const cardBorder = isTechnical ? `1px solid ${theme.primary}` : `1px solid ${theme.cardBorder}`;
          const cardShadow = isTechnical ? theme.glowEffect : theme.cardShadow;
          
          return (
            <div 
              className="metric-card" 
              key={index}
              style={{
                background: cardBg,
                border: cardBorder,
                boxShadow: cardShadow,
                borderRadius: '16px',
                padding: '20px 24px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                height: '100%',
                boxSizing: 'border-box',
              }}
            >
              <div className="metric-top" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                <EditableText 
                  slide={slide} 
                  zoneKey={cellKeys[index]} 
                  value={card.label} 
                  className="metric-label" 
                  as="span" 
                  style={{
                    color: isTechnical ? '#FFFFFF' : theme.textMuted,
                    fontWeight: 600,
                    fontSize: '15px',
                  }}
                />
                {card.change && (
                  <span 
                    className={`metric-trend ${isUp ? "trend-up" : "trend-down"}`}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '4px 10px',
                      borderRadius: '999px',
                      fontSize: '13px',
                      fontWeight: 700,
                      background: isUp ? (isTechnical ? 'rgba(0,212,255,0.15)' : '#DCFCE7') : (isTechnical ? 'rgba(255,0,110,0.15)' : '#FEE2E2'),
                      color: isUp ? (isTechnical ? '#00D4FF' : '#15803d') : (isTechnical ? '#FF006E' : '#b91c1c'),
                    }}
                  >
                    {isUp ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                    {card.change}
                  </span>
                )}
              </div>
              <EditableText 
                slide={slide} 
                zoneKey={cellKeys[index]} 
                value={card.value} 
                className="metric-value" 
                as="h2" 
                style={{
                  color: isTechnical ? '#FFFFFF' : theme.textHeading,
                  fontWeight: 700,
                  fontSize: '32px',
                  margin: '12px 0 0 0',
                }}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
};
