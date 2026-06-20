import React from "react";
import type { Slide } from "../types";
import { parseBulletPoint } from "../types";
import {
  Lightbulb,
  Cog,
  Rocket,
  Target,
  Search,
  Layers,
} from "lucide-react";
import { SlideTheme } from "../utils/themeUtils";
import { DecorativeElement } from "../components/DecorativeElement";
import SlideHeading from "../components/SlideHeading";

interface LayoutProps {
  slide: Slide;
  theme: SlideTheme;
}

const STEP_ICONS = [Search, Lightbulb, Cog, Layers, Rocket, Target];

/**
 * ProcessSlide – Numbered step layout with icon per step.
 * Linear arrangement with connector arrows.
 */
export const ProcessSlide: React.FC<LayoutProps> = ({ slide, theme }) => {
  const zone = slide.zone_content || {};

  const title = zone.title || slide.title || "Process";
  const subtitle = zone.subtitle;

  const defaultSteps = [
    { title: "Research", body: "Gather requirements, analyze existing data, and identify constraints." },
    { title: "Design", body: "Create wireframes, define architecture, and establish design tokens." },
    { title: "Build", body: "Implement core modules, integrate APIs, and write unit tests." },
    { title: "Test", body: "Run QA cycles, performance benchmarks, and user acceptance testing." },
    { title: "Deploy", body: "Release to staging, monitor metrics, and roll out to production." },
  ];

  let steps = zone.steps || null;
  if (Array.isArray(steps) && steps.length > 0 && typeof steps[0] === "string") {
    steps = (steps as string[]).map((item: string, idx: number) => {
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
      steps = listEl.items.map((item, i) => {
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

  // Cap at 5 steps for linear horizontal layout constraints
  const finalSteps = steps.slice(0, 5);

  if (theme.tone === "professional") {
    const profSteps = steps.slice(0, 4);
    return (
      <div 
        className="layout-container process-layout professional-process"
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
        <div className="layout-header" style={{ marginBottom: '24px' }}>
          <SlideHeading
            title={title}
            icon_emoji={slide.icon_emoji}
            theme={theme}
            slide={slide}
            zoneKey="title"
            style={{ marginBottom: 0 }}
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
          {subtitle && (
            <p 
              className="layout-subtitle"
              style={{
                color: '#646464',
                fontWeight: '400',
                fontSize: '16px',
                margin: 0,
              }}
            >
              {subtitle}
            </p>
          )}
        </div>

        <div className="process-steps-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flex: 1, width: '100%' }}>
          {profSteps.map((step: any, idx: number) => {
            const isLast = idx === profSteps.length - 1;
            
            return (
              <React.Fragment key={idx}>
                <div 
                  className="process-step-card"
                  style={{
                    background: '#F5F5F5',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                    padding: '24px 16px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    textAlign: 'center',
                    flex: 1,
                    position: 'relative',
                    height: '80%',
                    boxSizing: 'border-box',
                    justifyContent: 'flex-start',
                  }}
                >
                  {/* Step number in yellow circle on top */}
                  <div style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '50%',
                    backgroundColor: '#FFD600',
                    color: '#141414',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: '800',
                    fontSize: '12px',
                    marginBottom: '16px',
                    boxShadow: 'none'
                  }}>
                    0{idx + 1}
                  </div>

                  <h3 className="process-step-title" style={{ color: '#141414', fontSize: '16px', fontWeight: 700, margin: '0 0 12px 0' }}>{step.title}</h3>
                  <p className="process-step-body" style={{ color: '#646464', fontSize: '13px', margin: 0, lineHeight: 1.4 }}>{step.body}</p>
                </div>
                {!isLast && (
                  <div className="process-connector" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, width: '24px', position: 'relative' }}>
                    {/* Yellow line connector */}
                    <div style={{
                      width: '100%',
                      height: '2px',
                      backgroundColor: '#FFD600',
                    }} />
                    {/* Small horizontal chevron icon in circle */}
                    <div style={{
                      position: 'absolute',
                      width: '16px',
                      height: '16px',
                      borderRadius: '50%',
                      backgroundColor: '#FFD600',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#141414',
                      zIndex: 1,
                    }}>
                      <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="9 18 15 12 9 6" />
                      </svg>
                    </div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    );
  }

  const isTechnical = theme.decorativeShape === "glow";

  const cardBorder = isTechnical ? `1px solid ${theme.primary}` : `1px solid ${theme.cardBorder}`;
  const cardShadow = isTechnical ? theme.glowEffect : theme.cardShadow;

  return (
    <div 
      className="layout-container process-layout"
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

      <div className="process-steps-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', height: 'calc(100% - 140px)', width: '100%' }}>
        {finalSteps.map((step: any, idx: number) => {
          const Icon = STEP_ICONS[idx % STEP_ICONS.length];
          const isLast = idx === finalSteps.length - 1;
          
          return (
            <React.Fragment key={idx}>
              <div 
                className="process-step-card"
                style={{
                  background: theme.cardBackground,
                  border: cardBorder,
                  boxShadow: cardShadow,
                  borderRadius: '16px',
                  padding: '24px 16px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  textAlign: 'center',
                  flex: 1,
                  position: 'relative',
                  height: '85%',
                  justifyContent: 'space-between',
                  boxSizing: 'border-box',
                }}
              >
                <div className="process-step-number" style={{ color: theme.primary, fontWeight: 800, fontSize: '20px' }}>{String(idx + 1).padStart(2, "0")}</div>
                <div 
                  className="process-step-icon-wrapper"
                  style={{
                    background: theme.iconBg,
                    color: theme.iconColor,
                    borderRadius: '50%',
                    width: '48px', height: '48px',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '12px 0',
                  }}
                >
                  <Icon size={22} />
                </div>
                <h3 className="process-step-title" style={{ color: isTechnical ? '#FFFFFF' : theme.textHeading, fontSize: '15px', fontWeight: 700, margin: '0 0 8px 0' }}>{step.title}</h3>
                <p className="process-step-body" style={{ color: isTechnical ? '#E2E8F0' : theme.textBody, fontSize: '12px', margin: 0, lineHeight: 1.4 }}>{step.body}</p>
              </div>
              {!isLast && (
                <div className="process-connector" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <svg width="24" height="20" viewBox="0 0 36 20" fill="none">
                    <path
                      d="M0 10 H28 L22 4 M28 10 L22 16"
                      stroke={theme.primary}
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
