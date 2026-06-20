import React, { useMemo, useEffect } from "react";
import type { TemplateTokens } from "../types";

/** Default theme – sleek dark-blue professional palette */
export const DEFAULT_TOKENS: TemplateTokens = {
  colorPrimary: "#FFD600", // Yellow accent
  colorSecondary: "#141414", // Black/Dark
  colorBackground: "#FFFFFF", // White background
  colorSurface: "#F5F5F5", // Light-gray surface card
  colorText: "#141414", // Dark body text
  colorTextMuted: "#646464", // Muted text
  fontHeading: "'Montserrat', 'Inter', system-ui, sans-serif",
  fontBody: "'Inter', system-ui, sans-serif",
  radiusCard: "8px",
  radiusBadge: "4px",
  logoPosition: "bottom-left",
  footerText: "Executive Strategy Report",
  tone: "professional",
};

/** Get premium layout tokens based on tone */
export const getThemeTokens = (tone: string): TemplateTokens => {
  const normalized = (tone || "").toLowerCase();
  if (normalized === "creative") {
    return {
      colorPrimary: "#d946ef", // Fuchsia
      colorSecondary: "#e11d48", // Rose
      colorBackground: "#0f0728", // Deep Indigo/Fuchsia Dark
      colorSurface: "rgba(31, 18, 65, 0.6)", // Glass card
      colorText: "#fdf4ff",
      colorTextMuted: "#d8b4fe",
      fontHeading: "'Outfit', sans-serif",
      fontBody: "'Inter', sans-serif",
      radiusCard: "16px",
      radiusBadge: "24px",
      logoPosition: "bottom-left",
      footerText: "Creative Presentation",
      tone: "creative",
    };
  } else if (normalized === "lavish") {
    return {
      colorPrimary: "#43dfff",
      colorSecondary: "#4f7dff",
      colorBackground: "#07111f",
      colorSurface: "rgba(13, 31, 55, 0.72)",
      colorText: "#f8fbff",
      colorTextMuted: "#b6c7e6",
      fontHeading: "'Plus Jakarta Sans', sans-serif",
      fontBody: "'Inter', sans-serif",
      radiusCard: "4px",
      radiusBadge: "4px",
      logoPosition: "top-left",
      footerText: "LAVISH TECHNOLOGY TEMPLATE",
      tone: "lavish",
    };
  } else if (normalized === "technical") {
    return {
      colorPrimary: "#10b981", // Emerald Green
      colorSecondary: "#06b6d4", // Cyan
      colorBackground: "#030712", // Futuristic Black
      colorSurface: "rgba(17, 24, 39, 0.7)", // Tech card
      colorText: "#f9fafb",
      colorTextMuted: "#9ca3af",
      fontHeading: "'Space Grotesk', sans-serif",
      fontBody: "'Inter', sans-serif",
      radiusCard: "8px",
      radiusBadge: "4px",
      logoPosition: "bottom-left",
      footerText: "Technical Documentation",
      tone: "technical",
    };
  } else if (normalized === "academic") {
    return {
      colorPrimary: "#78350f", // Warm Amber/Brown
      colorSecondary: "#9d174d",
      colorBackground: "#fafaf9", // Warm editorial book paper
      colorSurface: "#f5f5f4", // Light stone card
      colorText: "#1c1917", // Charcoal text
      colorTextMuted: "#6b6661",
      fontHeading: "'Playfair Display', serif",
      fontBody: "'Lora', serif",
      radiusCard: "12px",
      radiusBadge: "30px",
      logoPosition: "bottom-left",
      footerText: "Academic Research Portfolio",
      tone: "academic",
    };
  } else if (normalized === "education") {
    return {
      colorPrimary: "#f5c518", // Bright Yellow (chalk accent)
      colorSecondary: "#e53935", // Chalk Red
      colorBackground: "#2d2d2d", // Dark chalkboard
      colorSurface: "rgba(55, 55, 55, 0.7)", // Chalkboard card surface
      colorText: "#ffffff", // White chalk text
      colorTextMuted: "#c8c8c8", // Light chalk muted
      fontHeading: "Georgia, serif", // Classroom chalkboard serif style
      fontBody: "Georgia, serif",
      radiusCard: "14px",
      radiusBadge: "20px",
      logoPosition: "bottom-left",
      footerText: "University Education Template",
      tone: "education",
    };
  } else if (normalized === "ecommerce" || normalized === "e-commerce") {
    return {
      colorPrimary: "#ff6b6b", // Coral/Salmon
      colorSecondary: "#a855f7", // Vivid Purple
      colorBackground: "linear-gradient(135deg, #ff6b6b 0%, #a855f7 50%, #3b82f6 100%)", // Multi-color gradient
      colorSurface: "rgba(255, 255, 255, 0.95)", // White floating card
      colorText: "#1e1b38", // Dark text (on white card)
      colorTextMuted: "#6b7280", // Gray muted
      fontHeading: "'Poppins', sans-serif",
      fontBody: "'Inter', sans-serif",
      radiusCard: "24px",
      radiusBadge: "30px",
      logoPosition: "bottom-left",
      footerText: "E-Commerce Showcase",
      tone: "ecommerce",
    };
  } else if (normalized === "neumorphism") {
    return {
      colorPrimary: "#122A6E",
      colorSecondary: "#556080",
      colorBackground: "#F1F4F7",
      colorSurface: "#F1F4F7",
      colorText: "#122A6E",
      colorTextMuted: "#556080",
      fontHeading: "'Poppins', 'Montserrat', sans-serif",
      fontBody: "'Poppins', 'Inter', sans-serif",
      radiusCard: "24px",
      radiusBadge: "30px",
      logoPosition: "bottom-left",
      footerText: "Neumorphic Tactile Strategy",
      tone: "neumorphism",
    };
  } else {
    // Professional (default)
    return DEFAULT_TOKENS;
  }
};

/**
 * Converts TemplateTokens into a flat CSS-variable style object so all
 * children can reference `var(--theme-colorPrimary)` etc.
 */
function tokensToCssVars(tokens: TemplateTokens): React.CSSProperties {
  const isDark = ["#f8fafc", "#faf5ff", "#f9fafb", "#ffffff"].includes(tokens.colorText.toLowerCase()) || 
                 ["#0b0f19", "#0f0728", "#030712", "#2d2d2d"].includes(tokens.colorBackground.toLowerCase()) ||
                 tokens.colorBackground.includes("gradient");
  
  return {
    "--theme-colorPrimary": tokens.colorPrimary,
    "--theme-colorSecondary": tokens.colorSecondary,
    "--theme-colorBackground": tokens.colorBackground,
    "--theme-colorSurface": tokens.colorSurface,
    "--theme-colorText": tokens.colorText,
    "--theme-colorTextMuted": tokens.colorTextMuted,
    "--theme-fontHeading": tokens.fontHeading,
    "--theme-fontBody": tokens.fontBody,
    "--theme-radiusCard": tokens.radiusCard,
    "--theme-radiusBadge": tokens.radiusBadge,
    "--theme-borderCard": isDark ? "1px solid rgba(255, 255, 255, 0.09)" : "1px solid rgba(15, 23, 42, 0.08)",
    "--theme-borderCardHover": isDark ? "1px solid rgba(255, 255, 255, 0.18)" : "1px solid rgba(15, 23, 42, 0.15)",
    "--theme-cardShadow": isDark ? "0 10px 30px -10px rgba(0, 0, 0, 0.5)" : "0 8px 24px -8px rgba(15, 23, 42, 0.08)",
  } as React.CSSProperties;
}

export const ThemeContext = React.createContext<TemplateTokens>(DEFAULT_TOKENS);

interface ThemeProviderProps {
  tokens?: Partial<TemplateTokens>;
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ tokens, children }) => {
  const merged = useMemo<TemplateTokens>(
    () => ({ ...DEFAULT_TOKENS, ...tokens }),
    [tokens]
  );

  const cssVars = useMemo(() => tokensToCssVars(merged), [merged]);

  // Inject Google Fonts dynamic loading
  useEffect(() => {
    const linkId = "theme-google-fonts";
    let link = document.getElementById(linkId) as HTMLLinkElement;
    if (!link) {
      link = document.createElement("link");
      link.id = linkId;
      link.rel = "stylesheet";
      document.head.appendChild(link);
    }
    link.href = "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@700;800&family=Outfit:wght@700;800&family=Space+Grotesk:wght@700&family=Playfair+Display:ital,wght@0,700;1,700&family=Lora:wght@400;500&family=Caveat:wght@400;500;600;700&family=Patrick+Hand&family=Poppins:wght@400;500;600;700;800&family=Montserrat:wght@400;500;600;700;800&display=swap";
  }, []);

  const toneClass = merged.tone ? `theme-${merged.tone.toLowerCase()}` : "theme-professional";

  return (
    <ThemeContext.Provider value={merged}>
      <div className={`theme-root ${toneClass}`} style={cssVars}>
        {children}
      </div>
    </ThemeContext.Provider>
  );
};

export function useTheme(): TemplateTokens {
  return React.useContext(ThemeContext);
}
