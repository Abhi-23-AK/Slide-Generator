import React from "react";
import type { Slide } from "../types";
import { Award, Compass, Zap, Image as ImageIcon } from "lucide-react";
import { parseBulletPoint } from "../types";
import { EditableText } from "./EditableText";
import { useEditorStore } from "../store/editorStore";
import { SlideTheme } from "../utils/themeUtils";
import { DecorativeElement } from "../components/DecorativeElement";
import SlideHeading from "../components/SlideHeading";

interface LayoutProps {
  slide: Slide;
  theme: SlideTheme;
}

export const ThreeColumnLayout: React.FC<LayoutProps> = ({ slide, theme }) => {
  const { selectedZoneKey, selectZone, updateSlideZone } = useEditorStore();
  const zone = slide.zone_content || {};

  // Extract columns
  const defaultCols = [
    {
      heading: "Discovery",
      text: "Identify user needs, target demographics, and market opportunities through meticulous research.",
      icon: "01",
    },
    {
      heading: "Strategy",
      text: "Formulate concrete blueprints, design guidelines, and system architectures to guide development.",
      icon: "02",
    },
    {
      heading: "Execution",
      text: "Develop, review, test, and release modular solutions following industry-best practices.",
      icon: "03",
    },
  ];

  // Try to extract from elements if zone content is absent
  let columns = zone.columns || null;
  if (!columns && (zone.col_1 || zone.col_2 || zone.col_3)) {
    const parsed1 = parseBulletPoint(zone.col_1 || "");
    const parsed2 = parseBulletPoint(zone.col_2 || "");
    const parsed3 = parseBulletPoint(zone.col_3 || "");
    columns = [
      { heading: parsed1.title || "Focus Area 1", text: parsed1.description || "", icon: "01" },
      { heading: parsed2.title || "Focus Area 2", text: parsed2.description || "", icon: "02" },
      { heading: parsed3.title || "Focus Area 3", text: parsed3.description || "", icon: "03" },
    ];
  }
  if (!columns) {
    const listElement = slide.elements.find((el) => el.kind === "icon" || el.kind === "flow" || el.kind === "chart");
    if (listElement && listElement.items && listElement.items.length >= 3) {
      columns = listElement.items.slice(0, 3).map((item, idx) => {
        const parsed = parseBulletPoint(item);
        return {
          heading: parsed.title,
          text: parsed.description,
          icon: `0${idx + 1}`,
        };
      });
    } else {
      columns = defaultCols;
    }
  }

  // Ensure we have exactly 3 columns
  const finalColumns = columns.slice(0, 3);
  while (finalColumns.length < 3) {
    finalColumns.push(defaultCols[finalColumns.length]);
  }

  // Icons map helper
  const getIcon = (iconName: string, index: number) => {
    const icons = [<Award size={20} key={0} />, <Compass size={20} key={1} />, <Zap size={20} key={2} />];
    return icons[index % icons.length];
  };

  const isTechnical = theme.decorativeShape === "glow";

  return (
    <div 
      className="layout-container three-column-layout"
      style={{
        backgroundColor: slide.background || theme.slideBackground,
        fontFamily: theme.bodyFont,
        width: '100%', height: '100%',
        position: 'relative',
        boxSizing: 'border-box',
        overflow: 'hidden',
      }}
    >
      {/* Decorative background element */}
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

      <div className="three-column-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px', height: 'calc(100% - 140px)' }}>
        {finalColumns.map((col: any, index: number) => {
          const imgKey = `col_${index + 1}_image`;
          const colImage = zone[imgKey] || "";

          const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
            const file = e.target.files?.[0];
            if (file) {
              const reader = new FileReader();
              reader.onloadend = () => {
                updateSlideZone(slide.id, imgKey, reader.result);
              };
              reader.readAsDataURL(file);
            }
          };

          const handleHeadingInput = (e: React.FormEvent<HTMLHeadingElement>) => {
            const newHeading = e.currentTarget.innerText;
            updateSlideZone(slide.id, `col_${index + 1}`, `${newHeading}: ${col.text}`);
          };

          const handleTextInput = (e: React.FormEvent<HTMLParagraphElement>) => {
            const newText = e.currentTarget.innerText;
            updateSlideZone(slide.id, `col_${index + 1}`, `${col.heading}: ${newText}`);
          };

          const isPill = col.icon === "01" || col.icon === "02" || col.icon === "03";

          const cardBg = isTechnical && theme.gradientCards 
            ? theme.gradientCards[index % theme.gradientCards.length] 
            : theme.cardBackground;
          const cardBorder = isTechnical ? 'none' : `1px solid ${theme.cardBorder}`;
          const cardShadow = isTechnical ? theme.glowEffect : theme.cardShadow;
          const cardTextColor = isTechnical ? '#FFFFFF' : theme.textBody;
          const headingColor = isTechnical ? '#FFFFFF' : theme.textHeading;

          return (
            <div 
              className="three-column-card" 
              key={index} 
              style={{ 
                padding: "24px 20px",
                background: cardBg,
                border: cardBorder,
                boxShadow: cardShadow,
                borderRadius: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                height: '100%',
                boxSizing: 'border-box',
              }}
            >
              <div className="flex items-start justify-between w-full mb-1" style={{ display: "flex", width: "100%", justifyContent: "space-between", alignItems: "center", minHeight: "36px" }}>
                {isPill ? (
                  <span 
                    className="text-xs font-medium text-white px-2.5 py-0.5 rounded-full" 
                    style={{ 
                      fontSize: "13px", 
                      fontWeight: 500, 
                      backgroundColor: theme.primary, 
                      color: theme.textOnPrimary, 
                      padding: "2px 8px", 
                      borderRadius: "999px" 
                    }}
                  >
                    {col.icon}
                  </span>
                ) : (
                  <div 
                    className="three-column-icon-wrapper"
                    style={{
                      background: theme.iconBg,
                      color: theme.iconColor,
                      borderRadius: '50%',
                      width: 48, height: 48,
                      display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}
                  >
                    {getIcon(col.icon || "", index)}
                  </div>
                )}
              </div>

              <div className="three-column-card-content flex flex-col gap-1.5" style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1, minWidth: 0 }}>
                <h3
                  contentEditable
                  suppressContentEditableWarning
                  className={`text-base font-semibold editable-zone ${selectedZoneKey === `col_${index + 1}` ? "selected" : ""}`}
                  style={{ color: headingColor, margin: 0, outline: "none", fontSize: "18px", fontWeight: 600 }}
                  onFocus={() => selectZone(`col_${index + 1}`)}
                  onBlur={handleHeadingInput}
                  onInput={handleHeadingInput}
                >
                  {col.heading}
                </h3>
                <p
                  contentEditable
                  suppressContentEditableWarning
                  className={`text-sm font-normal leading-[1.65] editable-zone ${selectedZoneKey === `col_${index + 1}` ? "selected" : ""}`}
                  style={{ color: cardTextColor, margin: 0, outline: "none", fontSize: "14px", fontWeight: 400, lineHeight: 1.6 }}
                  onFocus={() => selectZone(`col_${index + 1}`)}
                  onBlur={handleTextInput}
                  onInput={handleTextInput}
                >
                  {col.text}
                </p>
              </div>
              
              <div
                className="three-column-image-wrapper"
                onClick={() => document.getElementById(`three-col-file-${index}`)?.click()}
                style={{ 
                  marginTop: "auto",
                  width: '80px', height: '80px',
                  borderRadius: '50%',
                  overflow: 'hidden',
                  cursor: 'pointer',
                  border: isTechnical ? `2px solid ${theme.primary}` : `1px solid ${theme.cardBorder}`,
                  boxShadow: isTechnical ? theme.glowEffect : undefined,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: isTechnical ? '#111827' : 'rgba(0,0,0,0.02)',
                  alignSelf: 'center',
                }}
              >
                {colImage ? (
                  <img src={colImage} alt={`Column ${index + 1}`} className="three-column-circle-image" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                  <div className="three-column-image-placeholder" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: theme.textMuted }}>
                    <ImageIcon size={20} />
                    <span style={{ fontSize: "10px", fontWeight: 600, marginTop: '4px' }}>Add Image</span>
                  </div>
                )}
              </div>
              <input
                type="file"
                id={`three-col-file-${index}`}
                accept="image/*"
                style={{ display: "none" }}
                onChange={handleFileChange}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
};
