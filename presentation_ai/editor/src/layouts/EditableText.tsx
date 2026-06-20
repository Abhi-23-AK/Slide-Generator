import React, { useEffect, useRef } from "react";
import type { Slide, SlideElement } from "../types";
import { useEditorStore } from "../store/editorStore";

type EditableTextProps = {
  slide: Slide;
  zoneKey: string;
  value: string;
  className?: string;
  as?: "h1" | "h2" | "p" | "span" | "div";
  placeholder?: string;
  style?: React.CSSProperties;
};

export const EditableText: React.FC<EditableTextProps> = ({
  slide,
  zoneKey,
  value,
  className,
  as = "div",
  placeholder = "Add text",
  style: passedStyle,
}) => {
  const ref = useRef<HTMLElement | null>(null);
  const { selectedZoneKey, selectZone, updateSlideZone } = useEditorStore();
  const Tag = as;
  const style = (slide.zone_content?.__styles?.[zoneKey] || {}) as Partial<SlideElement>;

  useEffect(() => {
    if (ref.current && ref.current.innerText !== value) {
      ref.current.innerText = value || "";
    }
  }, [value]);

  const mergedStyle: React.CSSProperties = {
    ...passedStyle,
    fontSize: style.fontSize ? `${style.fontSize}px` : passedStyle?.fontSize,
    fontWeight: style.fontWeight ? (style.fontWeight as any) : passedStyle?.fontWeight,
    color: style.color ? style.color : passedStyle?.color,
    WebkitTextFillColor: style.color ? style.color : (passedStyle?.color || passedStyle?.WebkitTextFillColor),
    textAlign: style.textAlign ? (style.textAlign as any) : passedStyle?.textAlign,
  };

  return (
    <Tag
      ref={ref as any}
      className={`${className || ""} editable-zone ${selectedZoneKey === zoneKey ? "selected" : ""}`}
      contentEditable
      suppressContentEditableWarning
      data-placeholder={placeholder}
      style={mergedStyle}
      onPointerDown={(event) => {
        event.stopPropagation();
        selectZone(zoneKey);
      }}
      onFocus={() => selectZone(zoneKey)}
      onInput={(event) => {
        updateSlideZone(slide.id, zoneKey, event.currentTarget.innerText);
      }}
      onPaste={(event) => {
        event.stopPropagation();
      }}
    >
      {value}
    </Tag>
  );
};
