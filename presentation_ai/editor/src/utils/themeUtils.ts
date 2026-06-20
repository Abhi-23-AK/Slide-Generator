export interface SlideTheme {
  background: string;
  slideBackground: string;
  primary: string;
  primaryDark: string;
  secondary: string;
  accent: string;
  textHeading: string;
  textBody: string;
  textMuted: string;
  textOnPrimary: string;
  cardBackground: string;
  cardBorder: string;
  cardShadow: string;
  iconBg: string;
  iconColor: string;
  buttonBg: string;
  buttonText: string;
  headingTransform: string;
  headingWeight: string;
  headingFont: string;
  bodyFont: string;
  decorativeShape: string;
  bulletColor: string;
  timelineColor: string;
  chartColors: string[];
  footerBg: string;
  footerText: string;
  dividerColor: string;
  gradientCards?: string[];
  glowEffect?: string;
  hexColors?: string[];
  circleBorder?: string;
  panelBg?: string;
  panelText?: string;
  swotColors?: Record<string, string>;
  radiusCard?: string;
  radiusBadge?: string;
  tone?: string;
}

export const THEMES: Record<string, SlideTheme> = {
  professional: {
    background: "#FFFFFF",
    slideBackground: "#FFFFFF",
    primary: "#FFD600",
    primaryDark: "#D9B600",
    secondary: "#141414",
    accent: "#FFD600",
    textHeading: "#141414",
    textBody: "#646464",
    textMuted: "#9CA3AF",
    textOnPrimary: "#141414",
    cardBackground: "#F5F5F5",
    cardBorder: "#E5E7EB",
    cardShadow: "none",
    iconBg: "#FFD600",
    iconColor: "#141414",
    buttonBg: "#FFD600",
    buttonText: "#141414",
    headingTransform: "uppercase",
    headingWeight: "800",
    headingFont: "Montserrat, Inter, system-ui, sans-serif",
    bodyFont: "Inter, system-ui, sans-serif",
    decorativeShape: "rectangle",
    bulletColor: "#FFD600",
    timelineColor: "#FFD600",
    chartColors: ["#FFD600", "#141414", "#646464", "#D1D5DB"],
    footerBg: "#FFFFFF",
    footerText: "#9CA3AF",
    dividerColor: "#FFD600",
  },
  creative: {
    background: "#FFFFFF",
    slideBackground: "#FFFFFF",
    primary: "#4ECDC4",
    primaryDark: "#38B2AC",
    secondary: "#C9A0C0",
    accent: "#E8A0A0",
    textHeading: "#1A1A2E",
    textBody: "#2D3748",
    textMuted: "#718096",
    textOnPrimary: "#FFFFFF",
    cardBackground: "#FFFFFF",
    cardBorder: "#E2E8F0",
    cardShadow: "0 4px 12px rgba(78,205,196,0.15)",
    iconBg: "#4ECDC4",
    iconColor: "#FFFFFF",
    buttonBg: "#4ECDC4",
    buttonText: "#FFFFFF",
    headingTransform: "uppercase",
    headingWeight: "700",
    headingFont: "Inter, Poppins, sans-serif",
    bodyFont: "Inter, Poppins, sans-serif",
    decorativeShape: "hexagon",
    hexColors: ["#4ECDC4", "#C9A0C0", "#E8A0A0", "#F7DC6F"],
    bulletColor: "#4ECDC4",
    timelineColor: "#4ECDC4",
    chartColors: ["#4ECDC4", "#C9A0C0", "#E8A0A0", "#95E1D3"],
    footerBg: "#FFFFFF",
    footerText: "#999999",
    dividerColor: "#4ECDC4",
  },
  academic: {
    background: "#FFFFFF",
    slideBackground: "#FFFFFF",
    primary: "#2D7A4F",
    primaryDark: "#1F5C3A",
    secondary: "#E8F5EE",
    accent: "#48BB78",
    textHeading: "#1A2F23",
    textBody: "#2D3748",
    textMuted: "#718096",
    textOnPrimary: "#FFFFFF",
    cardBackground: "#FFFFFF",
    cardBorder: "#C6F6D5",
    cardShadow: "0 2px 8px rgba(45,122,79,0.10)",
    iconBg: "#E8F5EE",
    iconColor: "#2D7A4F",
    buttonBg: "#2D7A4F",
    buttonText: "#FFFFFF",
    headingTransform: "none",
    headingWeight: "700",
    headingFont: "Georgia, Inter, serif",
    bodyFont: "Inter, Segoe UI, sans-serif",
    decorativeShape: "circle",
    circleBorder: "#2D7A4F",
    panelBg: "#2D7A4F",
    panelText: "#FFFFFF",
    bulletColor: "#2D7A4F",
    timelineColor: "#2D7A4F",
    chartColors: ["#2D7A4F", "#48BB78", "#68D391", "#9AE6B4"],
    footerBg: "#FFFFFF",
    footerText: "#999999",
    dividerColor: "#2D7A4F",
    swotColors: {
      S: "#2D7A4F",
      W: "#E8F5EE",
      O: "#48BB78",
      T: "#1F5C3A",
    },
  },
  technical: {
    background: "#0A0E1A",
    slideBackground: "#0A0E1A",
    primary: "#00D4FF",
    primaryDark: "#0099CC",
    secondary: "#FF006E",
    accent: "#7B2FFF",
    textHeading: "#FFFFFF",
    textBody: "#CBD5E1",
    textMuted: "#94A3B8",
    textOnPrimary: "#0A0E1A",
    cardBackground: "#111827",
    cardBorder: "#1E3A5F",
    cardShadow: "0 4px 20px rgba(0,212,255,0.20)",
    iconBg: "linear-gradient(135deg,#00D4FF,#7B2FFF)",
    iconColor: "#FFFFFF",
    buttonBg: "linear-gradient(135deg,#00D4FF,#FF006E)",
    buttonText: "#FFFFFF",
    headingTransform: "none",
    headingWeight: "700",
    headingFont: "Inter, Rajdhani, sans-serif",
    bodyFont: "Inter, sans-serif",
    decorativeShape: "glow",
    gradientCards: [
      "linear-gradient(135deg,#1E3A8A,#7B2FFF)",
      "linear-gradient(135deg,#7B2FFF,#FF006E)",
      "linear-gradient(135deg,#0099CC,#00D4FF)",
    ],
    bulletColor: "#00D4FF",
    timelineColor: "#00D4FF",
    chartColors: ["#00D4FF", "#FF006E", "#7B2FFF", "#48BB78"],
    footerBg: "#0A0E1A",
    footerText: "#475569",
    dividerColor: "#00D4FF",
    glowEffect: "0 0 20px rgba(0,212,255,0.4)",
  },
  ecommerce: {
    background: "linear-gradient(135deg, #ff6b6b 0%, #a855f7 50%, #3b82f6 100%)",
    slideBackground: "linear-gradient(135deg, #ff6b6b 0%, #a855f7 50%, #3b82f6 100%)",
    primary: "#ff6b6b",
    primaryDark: "#ff6b6b",
    secondary: "#a855f7",
    accent: "#fbbf24",
    textHeading: "#1e1b38",
    textBody: "#1e1b38",
    textMuted: "#6b7280",
    textOnPrimary: "#ffffff",
    cardBackground: "#ffffff",
    cardBorder: "rgba(0,0,0,0.08)",
    cardShadow: "0 10px 30px -10px rgba(0, 0, 0, 0.15)",
    iconBg: "#ff6b6b",
    iconColor: "#ffffff",
    buttonBg: "#ff6b6b",
    buttonText: "#ffffff",
    headingTransform: "none",
    headingWeight: "700",
    headingFont: "Poppins, sans-serif",
    bodyFont: "Inter, sans-serif",
    decorativeShape: "circle",
    bulletColor: "#ff6b6b",
    timelineColor: "#ff6b6b",
    chartColors: ["#ff6b6b", "#a855f7", "#3b82f6"],
    footerBg: "transparent",
    footerText: "#6b7280",
    dividerColor: "#ff6b6b",
  },
  education: {
    background: "#2d2d2d",
    slideBackground: "#2d2d2d",
    primary: "#f5c518",
    primaryDark: "#f5c518",
    secondary: "#e53935",
    accent: "#f5c518",
    textHeading: "#ffffff",
    textBody: "#ffffff",
    textMuted: "#c8c8c8",
    textOnPrimary: "#2d2d2d",
    cardBackground: "rgba(55, 55, 55, 0.7)",
    cardBorder: "rgba(255,255,255,0.08)",
    cardShadow: "none",
    iconBg: "#f5c518",
    iconColor: "#2d2d2d",
    buttonBg: "#f5c518",
    buttonText: "#2d2d2d",
    headingTransform: "none",
    headingWeight: "700",
    headingFont: "Georgia, serif",
    bodyFont: "Georgia, serif",
    decorativeShape: "rectangle",
    bulletColor: "#f5c518",
    timelineColor: "#f5c518",
    chartColors: ["#f5c518", "#e53935"],
    footerBg: "#2d2d2d",
    footerText: "#c8c8c8",
    dividerColor: "#f5c518",
  },
  lavish: {
    background: "#07111f",
    slideBackground: "#07111f",
    primary: "#43dfff",
    primaryDark: "#43dfff",
    secondary: "#4f7dff",
    accent: "#43dfff",
    textHeading: "#f8fbff",
    textBody: "#f8fbff",
    textMuted: "#b6c7e6",
    textOnPrimary: "#07111f",
    cardBackground: "rgba(13, 31, 55, 0.72)",
    cardBorder: "rgba(255,255,255,0.08)",
    cardShadow: "none",
    iconBg: "#43dfff",
    iconColor: "#07111f",
    buttonBg: "#43dfff",
    buttonText: "#07111f",
    headingTransform: "none",
    headingWeight: "700",
    headingFont: "Plus Jakarta Sans, sans-serif",
    bodyFont: "Inter, sans-serif",
    decorativeShape: "rectangle",
    bulletColor: "#43dfff",
    timelineColor: "#43dfff",
    chartColors: ["#43dfff", "#4f7dff"],
    footerBg: "#07111f",
    footerText: "#b6c7e6",
    dividerColor: "#43dfff",
  },
  neumorphism: {
    background: "#F1F4F7",
    slideBackground: "#F1F4F7",
    primary: "#122A6E",
    primaryDark: "#0D1F52",
    secondary: "#556080",
    accent: "#FF5AA0",
    textHeading: "#122A6E",
    textBody: "#122A6E",
    textMuted: "#556080",
    textOnPrimary: "#FFFFFF",
    cardBackground: "#F1F4F7",
    cardBorder: "none",
    cardShadow: "9px 9px 16px #CDD2DC, -9px -9px 16px #FFFFFF",
    iconBg: "#FF5AA0",
    iconColor: "#FFFFFF",
    buttonBg: "#F1F4F7",
    buttonText: "#122A6E",
    headingTransform: "none",
    headingWeight: "300",
    headingFont: "Poppins, Montserrat, sans-serif",
    bodyFont: "Poppins, Inter, sans-serif",
    decorativeShape: "circle",
    bulletColor: "#122A6E",
    timelineColor: "#122A6E",
    chartColors: ["#FF5AA0", "#FFB43C", "#46BEFF", "#28DCB4"],
    footerBg: "#F1F4F7",
    footerText: "#556080",
    dividerColor: "#122A6E",
  }
};

export function getTheme(tone: string): SlideTheme {
  const key = tone.toLowerCase().replace("-", "");
  const baseTheme = THEMES[key] || THEMES.professional;
  return { 
    ...baseTheme, 
    tone: key,
    radiusCard: key === "professional" ? "8px" : (key === "creative" ? "16px" : (key === "lavish" ? "4px" : (key === "technical" ? "8px" : (key === "academic" ? "12px" : (key === "education" ? "14px" : (key === "neumorphism" ? "24px" : "24px")))))),
    radiusBadge: key === "professional" ? "4px" : (key === "creative" ? "24px" : (key === "lavish" ? "4px" : (key === "technical" ? "4px" : (key === "academic" ? "30px" : (key === "education" ? "20px" : (key === "neumorphism" ? "30px" : "30px"))))))
  };
}
