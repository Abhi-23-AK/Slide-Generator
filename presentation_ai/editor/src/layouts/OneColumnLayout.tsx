import React from "react";
import type { Slide } from "../types";
import { Image as ImageIcon } from "lucide-react";
import { EditableText } from "./EditableText";
import { SlideTheme } from "../utils/themeUtils";
import { DecorativeElement } from "../components/DecorativeElement";
import SlideHeading from "../components/SlideHeading";

interface LayoutProps {
  slide: Slide;
  theme: SlideTheme;
}

export const OneColumnLayout: React.FC<LayoutProps> = ({ slide, theme }) => {
  const zone = slide.zone_content || {};

  // Extract Headline (sub-heading)
  const headline =
    (zone.headline && zone.headline !== slide.title) ? zone.headline :
    "";

  // Extract Body — split into lines
  const bodyText =
    zone.body ||
    slide.elements.find((el) => el.kind === "text" && el.id !== "title-1" && el.fontWeight !== 700)?.text ||
    "Add body text or conclusion statement here to wrap up your thoughts in this layout.";

  const bodyLines = bodyText.split("\n").filter((line: string) => line.trim());

  // Extract Image
  const imageUrl = zone.image || slide.elements.find((el) => el.kind === "image")?.text;

  if (theme.tone === "professional") {
    const hasImage = imageUrl && !imageUrl.includes("Image placeholder");
    const textWidth = hasImage ? "60%" : "100%";
    const imageWidth = "40%";

    return (
      <div 
        className="layout-container one-column-layout professional-one-column"
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
        {/* Header */}
        <div className="layout-header" style={{ marginBottom: '24px' }}>
          <SlideHeading
            title={slide.title}
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
        </div>

        {/* Content row */}
        <div style={{ display: 'flex', flexDirection: 'row', gap: '40px', flex: 1, width: '100%', height: '100%' }}>
          {/* Left Column (Text & Bullets) */}
          <div style={{ width: textWidth, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            {headline && (
              <EditableText 
                slide={slide} 
                zoneKey="headline" 
                value={headline} 
                as="h2" 
                style={{
                  color: '#141414',
                  fontWeight: '700',
                  fontSize: '20px',
                  margin: '0 0 16px 0',
                }}
              />
            )}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {bodyLines.slice(0, 4).map((line: string, idx: number) => {
                let cleaned = line.trim();
                for (const prefix of ["•", "-", "*", "✓"]) {
                  if (cleaned.startsWith(prefix)) {
                    cleaned = cleaned.substring(prefix.length).trim();
                  }
                }
                return (
                  <div 
                    key={idx} 
                    style={{ 
                      color: '#646464',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px',
                      fontSize: '15px',
                      fontWeight: '400',
                      lineHeight: 1.4,
                    }}
                  >
                    <span style={{ color: '#FFD600', fontSize: '18px', fontWeight: 'bold', lineHeight: 1 }}>✓</span>
                    <EditableText slide={slide} zoneKey={`body`} value={cleaned} as="span" style={{ flex: 1 }} />
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column (Framed Image Card) */}
          {hasImage && (
            <div style={{ 
              width: imageWidth, 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              boxSizing: 'border-box'
            }}>
              <div style={{
                width: '100%',
                height: '320px',
                backgroundColor: '#F5F5F5',
                borderRadius: '8px',
                border: '1px solid #E5E7EB',
                padding: '12px',
                boxSizing: 'border-box',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <img 
                  src={imageUrl} 
                  alt="one-col visual" 
                  style={{ 
                    width: '100%', 
                    height: '100%', 
                    objectFit: 'cover', 
                    borderRadius: '6px',
                    border: '1px solid #E5E7EB'
                  }} 
                />
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div 
      className="layout-container one-column-layout"
      style={{
        backgroundColor: slide.background || theme.slideBackground,
        fontFamily: theme.bodyFont,
        width: '100%', height: '100%',
        position: 'relative',
        boxSizing: 'border-box',
        overflow: 'hidden',
      }}
    >
      {/* Decorative element in the top-right corner */}
      <DecorativeElement theme={theme} position={{ top: '60px', right: '80px' }} />

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

      <div className="one-column-hero" style={{ height: '340px', borderRadius: '12px', overflow: 'hidden', border: `1px solid ${theme.cardBorder}` }}>
        {imageUrl && !imageUrl.includes("Image placeholder") ? (
          <img src={imageUrl} alt="Hero" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        ) : (
          <div 
            className="one-column-hero-placeholder"
            style={{
              width: '100%', height: '100%',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              backgroundColor: theme.cardBackground,
              color: theme.textMuted,
              gap: '8px',
            }}
          >
            <ImageIcon size={36} />
            <span style={{ fontSize: '14px', fontWeight: 600 }}>Featured Image Area</span>
          </div>
        )}
      </div>

      <div className="one-column-content" style={{ marginTop: "24px" }}>
        {headline && (
          <div className="text-lg font-normal mb-4">
            <EditableText 
              slide={slide} 
              zoneKey="headline" 
              value={headline} 
              as="h2" 
              style={{
                color: theme.textHeading,
                fontWeight: '600',
                fontSize: '20px',
                margin: '0 0 16px 0',
              }}
            />
          </div>
        )}
        <div className="one-column-body flex flex-col gap-3" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {bodyLines.map((line: string, idx: number) => {
            const isChallenge = line.toLowerCase().startsWith("challenge:") || line.toLowerCase().startsWith("key challenge:") || line.toLowerCase().startsWith("problem:");
            if (isChallenge) {
              const colonIdx = line.indexOf(":");
              const label = colonIdx !== -1 ? line.substring(0, colonIdx + 1) : "Challenge:";
              const body = colonIdx !== -1 ? line.substring(colonIdx + 1) : line;
              return (
                <div 
                  key={idx} 
                  style={{ 
                    background: theme.decorativeShape === 'glow' ? '#1E293B' : '#DCFCE7', 
                    borderLeft: `4px solid ${theme.primary}`, 
                    borderRadius: "8px", 
                    padding: "12px 16px", 
                    display: "flex", 
                    gap: "12px", 
                    alignItems: "flex-start", 
                    marginTop: "4px",
                    boxShadow: theme.decorativeShape === 'glow' ? theme.glowEffect : undefined,
                  }}
                >
                  <span style={{ color: theme.bulletColor, fontSize: '18px', lineHeight: 1 }}>●</span>
                  <div style={{ fontSize: "15px", color: theme.textHeading, flex: 1, display: "flex", flexDirection: "row", flexWrap: "wrap", gap: "4px" }}>
                    <span style={{ fontWeight: 700 }}>{label}</span>
                    <EditableText slide={slide} zoneKey={`body`} value={body.trim()} as="span" style={{ fontWeight: 400, color: theme.textBody }} />
                  </div>
                </div>
              );
            }
            return (
              <div 
                key={idx} 
                className="flex items-start gap-3 text-base font-normal" 
                style={{ 
                  color: theme.textBody,
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  fontSize: '16px',
                  fontWeight: '400',
                }}
              >
                <span style={{ color: theme.bulletColor, fontSize: '18px', lineHeight: 1 }}>●</span>
                <EditableText slide={slide} zoneKey={`body`} value={line} as="span" style={{ flex: 1 }} />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
