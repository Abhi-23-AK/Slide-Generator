import React from "react";
import type { Slide } from "../types";
import { EditableText } from "./EditableText";
import { SlideTheme } from "../utils/themeUtils";
import { DecorativeElement } from "../components/DecorativeElement";
import SlideHeading from "../components/SlideHeading";

interface LayoutProps {
  slide: Slide;
  theme: SlideTheme;
}

export const HeroLayout: React.FC<LayoutProps> = ({ slide, theme }) => {
  const zone = slide.zone_content || {};

  const title = zone.title || slide.title || "Untitled Section";
  
  // Extract subtitle
  const subtitle =
    zone.subtitle ||
    slide.elements.find((el) => el.kind === "text" && el.id !== "title-1")?.text ||
    "Key overview and introduction to this presentation deck.";

  if (theme.tone === "professional") {
    const imageElement = slide.elements.find(el => el.kind === "image");
    const imgSource = zone.background_image || imageElement?.text || "";
    
    // Extract bullets from elements or zone_content
    const listElement = slide.elements.find(
      (el) => el.kind === "icon" || el.kind === "flow" || el.kind === "chart" || el.kind === "table"
    );
    const bullets = listElement?.items || [];
    const bulletList = zone.bullet_points || bullets;
    const subtitleText = zone.subtitle || bulletList[0] || subtitle;
    const bodyBullets = bulletList.slice(1, 3);

    return (
      <div className="hero-layout professional-hero" style={{
        display: 'flex',
        flexDirection: 'row',
        width: '100%',
        height: '100%',
        backgroundColor: slide.background || '#FFFFFF',
        fontFamily: theme.bodyFont,
        overflow: 'hidden',
      }}>
        {/* Left column (25%) */}
        <div style={{
          width: '25%',
          height: '100%',
          backgroundColor: '#FFD600',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'flex-end',
          alignItems: 'center',
          padding: '24px',
          boxSizing: 'border-box',
          position: 'relative'
        }}>
          {/* Decorative design element or Leaf/Star SVG on upper portion */}
          <div style={{
            position: 'absolute',
            top: '40px',
            opacity: 0.8,
            color: '#141414'
          }}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
          </div>
          
          {/* Image card in lower portion */}
          <div style={{
            width: '100%',
            height: '180px',
            backgroundColor: '#F5F5F5',
            borderRadius: '8px',
            border: '1px solid #E5E7EB',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '20px',
            boxShadow: 'none'
          }}>
            {imgSource ? (
              <img src={imgSource} alt="hero visual" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#646464" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <polyline points="21 15 16 10 5 21"/>
              </svg>
            )}
          </div>
        </div>

        {/* Right column (75%) */}
        <div style={{
          width: '75%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: '60px 80px',
          boxSizing: 'border-box',
          textAlign: 'left',
          alignItems: 'flex-start'
        }}>
          <SlideHeading
            title={title}
            icon_emoji={slide.icon_emoji}
            theme={theme}
            slide={slide}
            zoneKey="title"
            style={{
              justifyContent: 'flex-start',
              marginBottom: '24px',
            }}
            textStyle={{
              color: '#141414',
              fontSize: '48px',
              fontWeight: '800',
              textAlign: 'left',
              lineHeight: 1.1,
              textTransform: 'uppercase',
              fontFamily: theme.headingFont,
            }}
          />
          
          {subtitleText && (
            <EditableText 
              slide={slide} 
              zoneKey="subtitle" 
              value={subtitleText} 
              className="hero-subtitle" 
              as="h2" 
              style={{
                color: '#646464',
                fontWeight: '700',
                fontSize: '20px',
                fontFamily: theme.bodyFont,
                textAlign: 'left',
                maxWidth: '650px',
                lineHeight: 1.3,
                marginBottom: '20px'
              }}
            />
          )}

          {bodyBullets.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {bodyBullets.map((bullet: string, idx: number) => (
                <div key={idx} style={{
                  color: '#646464',
                  fontSize: '14px',
                  fontFamily: theme.bodyFont,
                  lineHeight: 1.4,
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '8px'
                }}>
                  <span style={{ color: '#FFD600', fontWeight: 'bold' }}>✓</span>
                  <span>{bullet}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  const bgStyle: React.CSSProperties = {
    backgroundColor: slide.background || theme.slideBackground,
    fontFamily: theme.bodyFont,
    width: '100%',
    height: '100%',
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  };

  if (zone.background_image) {
    bgStyle.backgroundImage = `url(${zone.background_image})`;
    bgStyle.backgroundSize = "cover";
    bgStyle.backgroundPosition = "center";
  }

  // Determine if overlay is needed (for legibility with background image)
  const showOverlay = !!zone.background_image;

  return (
    <div className="hero-layout" style={bgStyle}>
      {showOverlay && <div className="hero-overlay" style={{ position: 'absolute', inset: 0, backgroundColor: 'rgba(0,0,0,0.4)', zIndex: 1 }} />}
      
      {/* Decorative corner elements */}
      {!zone.background_image && (
        <>
          <DecorativeElement theme={theme} position={{ top: '60px', left: '60px', zIndex: 2 }} />
          <DecorativeElement theme={theme} position={{ bottom: '60px', right: '60px', zIndex: 2 }} />
        </>
      )}

      <div className="hero-content" style={{ zIndex: 2, display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '40px' }}>
        <SlideHeading
          title={title}
          icon_emoji={slide.icon_emoji}
          theme={theme}
          slide={slide}
          zoneKey="title"
          style={{
            justifyContent: 'center',
            marginBottom: '24px',
          }}
          textStyle={{
            color: showOverlay ? '#FFFFFF' : theme.textHeading,
            fontSize: '54px',
            textAlign: 'center',
            flex: 'none',
          }}
        />
        <div style={{
          width: '60px', height: '4px',
          backgroundColor: theme.primary,
          borderRadius: '2px',
          marginBottom: '24px'
        }} />
        <EditableText 
          slide={slide} 
          zoneKey="subtitle" 
          value={subtitle} 
          className="hero-subtitle" 
          as="p" 
          style={{
            color: showOverlay ? 'rgba(255,255,255,0.85)' : theme.textMuted,
            fontWeight: '400',
            fontSize: '20px',
            fontFamily: theme.bodyFont,
            textAlign: 'center',
            maxWidth: '800px',
            lineHeight: 1.5,
          }}
        />
      </div>
    </div>
  );
};
