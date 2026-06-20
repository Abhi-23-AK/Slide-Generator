import React from "react";
import { SlideTheme } from "../utils/themeUtils";
import { Slide } from "../types";
import { EditableText } from "../layouts/EditableText";

interface SlideHeadingProps {
  title: string;
  icon_emoji?: string; // e.g. "🤖", "📊", "🚀"
  theme: SlideTheme;
  size?: 'large' | 'medium' | 'small';
  slide?: Slide;
  zoneKey?: string;
  color?: string;
  style?: React.CSSProperties;
  textStyle?: React.CSSProperties;
  emojiStyle?: React.CSSProperties;
}

const SlideHeading = ({ 
  title, 
  icon_emoji, 
  theme,
  size = 'large',
  slide,
  zoneKey,
  color,
  style,
  textStyle,
  emojiStyle,
}: SlideHeadingProps) => {
  
  const fontSizes = {
    large: '36px',   // main slide title
    medium: '24px',  // section heading
    small: '18px'    // card heading
  };

  const emojiSizes = {
    large: '42px', // ~1.2x of 36px
    medium: '28px', // ~1.2x of 24px
    small: '22px'   // ~1.2x of 18px
  };

  const currentFontSize = textStyle?.fontSize || fontSizes[size];
  
  // Calculate dynamic emoji size if custom fontSize is provided
  let currentEmojiSize = emojiSizes[size];
  if (textStyle?.fontSize && typeof textStyle.fontSize === 'string') {
    const fs = parseFloat(textStyle.fontSize);
    if (!isNaN(fs)) {
      currentEmojiSize = `${Math.round(fs * 1.2)}px`;
    }
  }

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      marginBottom: '20px',
      width: '100%',
      ...style
    }}>
      {/* EMOJI ICON */}
      {icon_emoji && (
        <span style={{
          fontSize: currentEmojiSize,
          lineHeight: 1,
          flexShrink: 0,
          ...emojiStyle
        }}>
          {icon_emoji}
        </span>
      )}
      
      {/* HEADING TEXT */}
      {slide && zoneKey ? (
        <EditableText
          slide={slide}
          zoneKey={zoneKey}
          value={title}
          as="h1"
          style={{
            fontSize: currentFontSize,
            fontWeight: theme.headingWeight as any,
            fontFamily: theme.headingFont,
            color: color || theme.textHeading,
            textTransform: theme.headingTransform as any,
            lineHeight: 1.2,
            margin: 0,
            ...textStyle
          }}
        />
      ) : (
        <h1 style={{
          fontSize: currentFontSize,
          fontWeight: theme.headingWeight as any,
          fontFamily: theme.headingFont,
          color: color || theme.textHeading,
          textTransform: theme.headingTransform as any,
          lineHeight: 1.2,
          margin: 0,
          ...textStyle
        }}>
          {title}
        </h1>
      )}
    </div>
  );
};

export default SlideHeading;
