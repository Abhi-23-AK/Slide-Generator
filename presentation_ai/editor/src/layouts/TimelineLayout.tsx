import React from "react";
import type { Slide } from "../types";
import { parseBulletPoint } from "../types";
import { SlideTheme } from "../utils/themeUtils";
import { DecorativeElement } from "../components/DecorativeElement";
import SlideHeading from "../components/SlideHeading";

interface LayoutProps {
  slide: Slide;
  theme: SlideTheme;
}

export const TimelineLayout: React.FC<LayoutProps> = ({ slide, theme }) => {
  const zone = slide.zone_content || {};

  const defaultEvents = [
    { date: "2024 Q1", title: "Discovery", description: "Establish core parameters and target personas." },
    { date: "2024 Q3", title: "Prototyping", description: "Build working mockups for focus feedback." },
    { date: "2025 Q1", title: "Beta Launch", description: "Open sandbox preview to early access users." },
    { date: "2025 Q4", title: "General Release", description: "Scale globally to production environments." },
  ];

  let events = zone.events || null;
  if (typeof events === "string") {
    events = events.split("\n").filter(Boolean).map((evt: string, idx: number) => {
      const defaultDate = `202${4 + idx} Q${(idx % 4) + 1}`;
      const parsed = parseBulletPoint(evt, defaultDate);
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
        const defaultDate = `202${4 + idx} Q${(idx % 4) + 1}`;
        const parsed = parseBulletPoint(item, defaultDate);
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

  // Cap at 4 events for horizontal spacing layout limits
  const finalEvents = events.slice(0, 4);
  while (finalEvents.length < 4) {
    finalEvents.push(defaultEvents[finalEvents.length]);
  }

  const isTechnical = theme.decorativeShape === "glow";

  const cardBorder = isTechnical ? `1px solid ${theme.primary}` : `1px solid ${theme.cardBorder}`;
  const cardShadow = isTechnical ? theme.glowEffect : theme.cardShadow;

  return (
    <div 
      className="layout-container timeline-layout"
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

      <div className="timeline-container" style={{ position: 'relative', height: 'calc(100% - 140px)', display: 'flex', alignItems: 'center' }}>
        <div className="timeline-track" style={{ position: 'absolute', left: 0, right: 0, height: '4px', backgroundColor: theme.primary, zIndex: 1 }} />
        <div className="timeline-events-wrapper" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', width: '100%', zIndex: 2 }}>
          {finalEvents.map((evt: any, index: number) => (
            <div className="timeline-event-node" key={index} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative' }}>
              {index % 2 === 0 ? (
                <>
                  <div className="timeline-date" style={{ color: theme.primary, fontWeight: 700, fontSize: '18px', marginBottom: '12px' }}>{evt.date}</div>
                  <div className="timeline-dot" style={{ width: '16px', height: '16px', borderRadius: '50%', backgroundColor: theme.primary, border: `4px solid ${theme.slideBackground}`, zIndex: 3, marginBottom: '12px' }} />
                  <div 
                    className="timeline-event-card"
                    style={{
                      background: theme.cardBackground,
                      border: cardBorder,
                      boxShadow: cardShadow,
                      borderRadius: '12px',
                      padding: '16px',
                      width: '80%',
                      textAlign: 'center',
                    }}
                  >
                    <h3 className="timeline-event-title" style={{ color: isTechnical ? '#FFFFFF' : theme.textHeading, fontSize: '16px', fontWeight: 700, margin: '0 0 8px 0' }}>{evt.title}</h3>
                    <p className="timeline-event-desc" style={{ color: isTechnical ? '#E2E8F0' : theme.textBody, fontSize: '13px', margin: 0, lineHeight: 1.4 }}>{evt.description}</p>
                  </div>
                </>
              ) : (
                <>
                  <div 
                    className="timeline-event-card" 
                    style={{ 
                      background: theme.cardBackground,
                      border: cardBorder,
                      boxShadow: cardShadow,
                      borderRadius: '12px',
                      padding: '16px',
                      width: '80%',
                      textAlign: 'center',
                      marginBottom: "12px" 
                    }}
                  >
                    <h3 className="timeline-event-title" style={{ color: isTechnical ? '#FFFFFF' : theme.textHeading, fontSize: '16px', fontWeight: 700, margin: '0 0 8px 0' }}>{evt.title}</h3>
                    <p className="timeline-event-desc" style={{ color: isTechnical ? '#E2E8F0' : theme.textBody, fontSize: '13px', margin: 0, lineHeight: 1.4 }}>{evt.description}</p>
                  </div>
                  <div className="timeline-dot" style={{ width: '16px', height: '16px', borderRadius: '50%', backgroundColor: theme.primary, border: `4px solid ${theme.slideBackground}`, zIndex: 3, marginBottom: '12px' }} />
                  <div className="timeline-date" style={{ color: theme.primary, fontWeight: 700, fontSize: '18px' }}>{evt.date}</div>
                </>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
