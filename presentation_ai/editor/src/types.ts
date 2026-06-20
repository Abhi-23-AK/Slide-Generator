export type ElementKind =
  | "text"
  | "shape"
  | "icon"
  | "image"
  | "flow"
  | "chart"
  | "table";

export type LayoutId =
  | "OneColumn"
  | "TwoColumn"
  | "ThreeColumn"
  | "FourGrid"
  | "Hero"
  | "Dashboard"
  | "Architecture"
  | "Timeline"
  | "Comparison"
  | "Process";

/** Design-system tokens injected as CSS custom properties by ThemeProvider */
export type TemplateTokens = {
  /** Primary brand colour */
  colorPrimary: string;
  /** Secondary accent colour */
  colorSecondary: string;
  /** Slide background colour (fallback) */
  colorBackground: string;
  /** Surface colour for cards / panels */
  colorSurface: string;
  /** Main text colour */
  colorText: string;
  /** Muted / secondary text colour */
  colorTextMuted: string;
  /** Heading font family */
  fontHeading: string;
  /** Body font family */
  fontBody: string;
  /** Border radius for cards */
  radiusCard: string;
  /** Border radius for buttons / badges */
  radiusBadge: string;
  /** Logo image URL */
  logoUrl?: string;
  /** Logo placement zone */
  logoPosition?: "top-left" | "top-right" | "bottom-left" | "bottom-right";
  /** Footer text */
  footerText?: string;
  /** Tone of the theme */
  tone?: string;
};

export type SlideContent = {
  layout_id?: LayoutId;
  layout_score?: number;
  content_type?: string;
  zone_content?: Record<string, any>;
  is_continuation?: boolean;
};

export type SlideElement = {
  id: string;
  kind: ElementKind;
  x: number;
  y: number;
  width: number;
  height: number;
  rotation?: number;
  text?: string;
  fill?: string;
  stroke?: string;
  color?: string;
  fontSize?: number;
  fontWeight?: number;
  textAlign?: "left" | "center" | "right" | "justify";
  radius?: number;
  items?: string[];
};

export type Slide = {
  id: string;
  title: string;
  background: string;
  elements: SlideElement[];
  layout_id?: LayoutId;
  layout_score?: number;
  content_type?: string;
  zone_content?: Record<string, any>;
  is_continuation?: boolean;
  content?: SlideContent;
  /** Per-slide number override (auto-assigned by SlideFrame if absent) */
  slideNumber?: number;
  icon_keyword?: string;
  icon_emoji?: string;
  bullet_points?: string[];
  visual_items?: string[];
  visual_type?: string;
  /** Draw.io XML for architecture diagram rendering */
  drawio_xml?: string;
  /** Speaker notes for this slide */
  speaker_notes?: string;
};

export type Deck = {
  title: string;
  slides: Slide[];
  /** Optional deck-level theme tokens */
  theme?: Partial<TemplateTokens>;
};

export type EditorSnapshot = {
  deck: Deck;
  selectedSlideId: string;
  selectedElementId?: string;
  selectedZoneKey?: string;
  zoom: number;
};

/** Structured changes returned by the AI agent endpoint */
export type AgentChanges = {
  background?: string;
  title?: string;
  layout_id?: LayoutId;
  zone_content?: Record<string, any>;
  zone_styles?: Record<string, Partial<SlideElement>>;
  elements?: Record<string, Partial<SlideElement>>;
};

/** A single message in the agent chat history */
export type AgentMessage = {
  id: string;
  role: "user" | "ai";
  text: string;
  timestamp: number;
};

/** Helper to parse a timeline or process step bullet point into date, title, description */
export function parseBulletPoint(bullet: string, defaultDate?: string): { date: string; title: string; description: string } {
  // Common date/phase prefixes like "2024 Q1", "Phase 1", "Step 3", "2024"
  const dateRegex = /^(Q[1-4]\s+\d{4}|\d{4}\s+Q[1-4]|\d{4}|Phase\s+\d+|Step\s+\d+|[A-Za-z]+\s+\d{4})[:\-\s]*/i;
  
  let date = defaultDate || "";
  let remaining = bullet.trim();
  
  const dateMatch = remaining.match(dateRegex);
  if (dateMatch) {
    date = dateMatch[1].trim();
    remaining = remaining.substring(dateMatch[0].length).trim();
  }
  
  const colonIndex = remaining.indexOf(":");
  const dashIndex = remaining.indexOf(" - ");
  
  let title = remaining;
  let description = "";
  
  if (colonIndex !== -1 && (dashIndex === -1 || colonIndex < dashIndex)) {
    title = remaining.substring(0, colonIndex).trim();
    description = remaining.substring(colonIndex + 1).trim();
  } else if (dashIndex !== -1) {
    title = remaining.substring(0, dashIndex).trim();
    description = remaining.substring(dashIndex + 3).trim();
  }
  
  if (!description) {
    const periodIndex = remaining.indexOf(".");
    if (periodIndex !== -1 && periodIndex < remaining.length - 1) {
      title = remaining.substring(0, periodIndex).trim();
      description = remaining.substring(periodIndex + 1).trim();
    }
  }

  // Final clean up and fallbacks
  if (!description) {
    description = title;
  }
  
  return { date, title, description };
}

/** Helper to parse a metric card bullet point into label, value, change, trend */
export function parseMetricBullet(bullet: string, index: number): { label: string; value: string; change?: string; trend?: "up" | "down" } {
  const parts = bullet.split(":");
  let label = `Metric ${index + 1}`;
  let rest = bullet.trim();
  
  if (parts.length > 1) {
    label = parts[0].trim();
    rest = parts.slice(1).join(":").trim();
  }
  
  let change: string | undefined = undefined;
  let trend: "up" | "down" = "up";
  
  const changeRegex = /\(([-+]\d+(?:\.\d+)?%?)(?:\s+\w+)?\)/;
  const match = rest.match(changeRegex);
  if (match) {
    change = match[1];
    rest = rest.replace(changeRegex, "").trim();
  } else {
    const bareChangeRegex = /\b([-+]\d+(?:\.\d+)?%?)\b/;
    const bareMatch = rest.match(bareChangeRegex);
    if (bareMatch) {
      change = bareMatch[1];
      rest = rest.replace(bareChangeRegex, "").trim();
    }
  }
  
  if (change && change.startsWith("-")) {
    trend = "down";
  }
  
  let value = rest.replace(/[.,\s]+$/, "").trim();
  if (!value) {
    value = "—";
  }
  
  return { label, value, change, trend };
}
