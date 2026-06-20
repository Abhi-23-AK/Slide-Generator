import { create } from "zustand";
import type { Deck, EditorSnapshot, ElementKind, Slide, SlideElement, LayoutId, AgentChanges } from "../types";
import { getThemeTokens } from "../layouts/ThemeProvider";
import { getTheme } from "../utils/themeUtils";

type EditorStore = EditorSnapshot & {
  past: EditorSnapshot[];
  future: EditorSnapshot[];
  canUndo: boolean;
  canRedo: boolean;
  selectedZoneKey?: string;
  selectSlide: (slideId: string) => void;
  selectElement: (elementId?: string) => void;
  selectZone: (zoneKey?: string) => void;
  setZoom: (zoom: number) => void;
  addSlide: () => void;
  addElement: (kind: ElementKind) => void;
  addImageElement: (src: string, x?: number, y?: number) => void;
  updateElement: (elementId: string, patch: Partial<SlideElement>) => void;
  updateSlideZone: (slideId: string, zoneKey: string, value: any) => void;
  updateSlideZoneStyle: (slideId: string, zoneKey: string, patch: Partial<SlideElement>) => void;
  deleteSelectedElement: () => void;
  updateSlideLayout: (slideId: string, layoutId?: LayoutId) => void;
  setDeck: (deck: Deck) => void;
  applyAgentChanges: (slideId: string, changes: AgentChanges) => void;
  pasteElement: (element: SlideElement, x?: number, y?: number) => void;
  addTextElementAt: (x: number, y: number) => void;
  undo: () => void;
  redo: () => void;
};

const uid = (prefix: string) => `${prefix}-${Math.random().toString(36).slice(2, 9)}`;

export const mapLayoutId = (id: string): LayoutId => {
  switch (id) {
    case "1-column": return "OneColumn";
    case "2-column": return "TwoColumn";
    case "3-column": return "ThreeColumn";
    case "4-grid": return "FourGrid";
    case "hero": return "Hero";
    case "dashboard": return "Dashboard";
    case "architecture": return "Architecture";
    case "timeline": return "Timeline";
    case "comparison": return "Comparison";
    case "process": return "Process";
    default: return "OneColumn";
  }
};

export const getZoneContentForLayout = (
  layoutId: LayoutId,
  title: string,
  bulletPoints: string[],
  visualType: string,
  visualItems: string[],
  originalZoneContent?: Record<string, any>
): Record<string, any> => {
  const zone_content: Record<string, any> = { ...(originalZoneContent || {}) };
  const bullet_points = bulletPoints || [];
  
  if (layoutId === "Hero") {
    zone_content.title = title;
    zone_content.subtitle = bullet_points[0] || "";
    zone_content.background_image = originalZoneContent?.background_image || visualItems?.[0] || "";
  } else if (layoutId === "OneColumn") {
    zone_content.headline = title;
    zone_content.body = bullet_points.join("\n");
    zone_content.image = originalZoneContent?.image || visualItems?.[0] || "";
  } else if (layoutId === "TwoColumn") {
    zone_content.title = title;
    zone_content.left_headline = originalZoneContent?.left_headline || "Key Points";
    zone_content.left_text = bullet_points[0] || "";
    zone_content.bullets = bullet_points.slice(1);
    
    zone_content.right_content = {
      kind: visualType !== "none" ? visualType : "placeholder",
      items: visualItems || [],
      text: originalZoneContent?.right_content?.text || visualItems?.[0] || ""
    };
  } else if (layoutId === "ThreeColumn") {
    zone_content.col_1 = bullet_points[0] || "";
    zone_content.col_2 = bullet_points[1] || "";
    zone_content.col_3 = bullet_points[2] || "";
    // Dynamically assign images for the columns if they exist in visualItems
    zone_content.col_1_image = originalZoneContent?.col_1_image || visualItems?.[0] || "";
    zone_content.col_2_image = originalZoneContent?.col_2_image || visualItems?.[1] || "";
    zone_content.col_3_image = originalZoneContent?.col_3_image || visualItems?.[2] || "";
  } else if (layoutId === "FourGrid") {
    zone_content.cell_tl = bullet_points[0] || "";
    zone_content.cell_tr = bullet_points[1] || "";
    zone_content.cell_bl = bullet_points[2] || "";
    zone_content.cell_br = bullet_points[3] || "";
  } else if (layoutId === "Dashboard") {
    zone_content.stat_row = bullet_points[0] || "Overview";
    zone_content.chart_area = "Dashboard Chart";
    zone_content.insight_area = bullet_points.slice(1).join("\n");
  } else if (layoutId === "Architecture") {
    zone_content.diagram_canvas = "Architecture Diagram";
    zone_content.labels = bullet_points.join("\n");
  } else if (layoutId === "Timeline") {
    zone_content.events = bullet_points.join("\n");
  } else if (layoutId === "Comparison") {
    zone_content.left_title = originalZoneContent?.left_title || visualItems?.[0] || "Option A";
    zone_content.right_title = originalZoneContent?.right_title || visualItems?.[1] || "Option B";
    zone_content.left_points = bullet_points.filter((_: any, i: number) => i % 2 === 0);
    zone_content.right_points = bullet_points.filter((_: any, i: number) => i % 2 !== 0);
  } else if (layoutId === "Process") {
    zone_content.steps = bullet_points;
  }
  
  return zone_content;
};

export const mapBackendDeckToReact = (backendDeck: any, tone: string = "Professional"): Deck => {
  const title = backendDeck.deck_title || "Generated Presentation";
  const themeTokens = getThemeTokens(tone);
  const slides: Slide[] = (backendDeck.slides || []).map((slide: any, index: number) => {
    const slideId = `slide-${index}-${Math.random().toString(36).slice(2, 9)}`;
    const layout_id = mapLayoutId(slide.layout_id);
    const bullet_points = slide.bullet_points || [];
    
    const isTemplateMode = backendDeck.template_mode === true;
    let zone_content = {};
    if (isTemplateMode) {
      zone_content = slide.zone_content || {};
      console.log(`[TEMPLATE MODE] slide index: ${index}, layout_id: ${layout_id}, zone keys:`, Object.keys(zone_content));
    } else {
      zone_content = layout_id 
        ? getZoneContentForLayout(
            layout_id, 
            slide.title || "", 
            bullet_points, 
            slide.visual_type || "none", 
            slide.visual_items || [],
            slide.zone_content
          ) 
        : {};
    }
 
    // When a layout is active, the layout component (ContentLayer) renders all
    // content via zone_content. Adding elements here would cause overlapping text.
    // Only create elements for slides WITHOUT a layout (generic canvas mode).
    const elements: SlideElement[] = [];
 
    if (!layout_id) {
      // No layout — use elements for positioning on the generic canvas
      elements.push({
        id: `title-${slideId}`,
        kind: "text",
        x: 64,
        y: 48,
        width: 740,
        height: 60,
        text: slide.title || "Untitled Slide",
        fontSize: 34,
        fontWeight: 700,
        color: "#172033"
      });
      if (bullet_points.length > 0) {
        elements.push({
          id: `body-${slideId}`,
          kind: "text",
          x: 64,
          y: 130,
          width: 600,
          height: 300,
          text: bullet_points.join("\n"),
          fontSize: 18,
          color: "#2f3a4a"
        });
      }
    }
 
    const theme = getTheme(tone);
 
    return {
      id: slideId,
      title: slide.title || `Slide ${index + 1}`,
      background: theme.slideBackground,
      layout_id,
      layout_score: slide.layout_score || 0.8,
      content_type: slide.slide_type || "content",
      zone_content,
      elements,
      is_continuation: slide.is_continuation || false,
      slideNumber: index + 1,
      icon_keyword: slide.icon_keyword || "",
      icon_emoji: slide.icon_emoji || "",
      bullet_points,
      visual_items: slide.visual_items || [],
      visual_type: slide.visual_type || "none",
      drawio_xml: slide.drawio_xml || undefined,
      speaker_notes: slide.speaker_notes || "",
    };
  });
 
  return {
    title,
    slides,
    theme: themeTokens,
  };
};


const initialDeck: Deck = {
  title: "Generated Presentation",
  slides: [
    {
      id: "slide-title",
      title: "Title",
      background: "#f8fafc",
      layout_id: "Hero",
      layout_score: 0.95,
      content_type: "title",
      zone_content: {
        title: "Generated Presentation",
        subtitle: "Edit text, visuals, charts, and diagrams on a positioned canvas."
      },
      elements: [
        {
          id: "title-1",
          kind: "text",
          x: 96,
          y: 144,
          width: 920,
          height: 92,
          text: "Generated Presentation",
          fontSize: 48,
          fontWeight: 700,
          color: "#172033",
        },
        {
          id: "subtitle-1",
          kind: "text",
          x: 100,
          y: 258,
          width: 760,
          height: 48,
          text: "Edit text, visuals, charts, and diagrams on a positioned canvas.",
          fontSize: 24,
          color: "#526071",
        },
      ],
    },
    {
      id: "slide-abstract",
      title: "Abstract",
      background: "#ffffff",
      layout_id: "TwoColumn",
      layout_score: 0.88,
      content_type: "abstract",
      zone_content: {
        title: "Abstract",
        left_text: "Summarize the generated deck here. This area behaves like a slide object, not normal document flow.",
        right_content: {
          kind: "icon",
          items: ["Context", "Insight", "Outcome"]
        }
      },
      elements: [
        {
          id: "abstract-title",
          kind: "text",
          x: 64,
          y: 48,
          width: 720,
          height: 58,
          text: "Abstract",
          fontSize: 34,
          fontWeight: 700,
          color: "#162033",
        },
        {
          id: "abstract-body",
          kind: "text",
          x: 74,
          y: 138,
          width: 470,
          height: 270,
          text: "Summarize the generated deck here. This area behaves like a slide object, not normal document flow.",
          fontSize: 22,
          color: "#2f3a4a",
        },
        {
          id: "abstract-icons",
          kind: "icon",
          x: 650,
          y: 130,
          width: 360,
          height: 240,
          fill: "#0f766e",
          color: "#ffffff",
          items: ["Context", "Insight", "Outcome"],
        },
      ],
    },
  ],
};

const initialSnapshot: EditorSnapshot = {
  deck: initialDeck,
  selectedSlideId: initialDeck.slides[0].id,
  selectedElementId: initialDeck.slides[0].elements[0].id,
  selectedZoneKey: undefined,
  zoom: 0.72,
};

const snapshotOf = (state: EditorStore): EditorSnapshot => ({
  deck: state.deck,
  selectedSlideId: state.selectedSlideId,
  selectedElementId: state.selectedElementId,
  selectedZoneKey: state.selectedZoneKey,
  zoom: state.zoom,
});

const withHistory = (
  state: EditorStore,
  patch: Partial<EditorSnapshot>
): Partial<EditorStore> => ({
  ...patch,
  past: [...state.past, snapshotOf(state)],
  future: [],
  canUndo: true,
  canRedo: false,
});

const selectedSlide = (deck: Deck, slideId: string) =>
  deck.slides.find((slide) => slide.id === slideId) ?? deck.slides[0];

const createElement = (kind: ElementKind): SlideElement => {
  const base = {
    id: uid(kind),
    kind,
    x: 130,
    y: 130,
    width: 280,
    height: 120,
    fill: "#e8f1ff",
    stroke: "#2563eb",
    color: "#172033",
    fontSize: 20,
    text: "New element",
  };

  if (kind === "shape") return { ...base, text: "", radius: 8 };
  if (kind === "icon") return { ...base, items: ["API", "LLM", "PPTX"], fill: "#0f766e", color: "#ffffff" };
  if (kind === "flow") return { ...base, items: ["Upload", "Parse", "Plan", "Render"], fill: "#f0f7ff" };
  if (kind === "chart") return { ...base, items: ["Speed", "Quality", "Reuse"], fill: "#dbeafe" };
  if (kind === "table") return { ...base, items: ["Input", "Processing", "Output"], fill: "#ffffff" };
  if (kind === "image") return { ...base, text: "Image placeholder", fill: "#eef2f7" };
  return base;
};

export const useEditorStore = create<EditorStore>((set, get) => ({
  ...initialSnapshot,
  past: [],
  future: [],
  canUndo: false,
  canRedo: false,

  selectSlide: (slideId) =>
    set({ selectedSlideId: slideId, selectedElementId: selectedSlide(get().deck, slideId).elements[0]?.id, selectedZoneKey: undefined }),
  selectElement: (elementId) => set({ selectedElementId: elementId, selectedZoneKey: undefined }),
  selectZone: (zoneKey) => set({ selectedZoneKey: zoneKey, selectedElementId: undefined }),
  setZoom: (zoom) => set({ zoom }),

  addSlide: () => {
    const state = get();
    const slide: Slide = {
      id: uid("slide"),
      title: "New Slide",
      background: "#ffffff",
      elements: [
        {
          id: uid("title"),
          kind: "text",
          x: 64,
          y: 48,
          width: 740,
          height: 60,
          text: "New Slide",
          fontSize: 34,
          fontWeight: 700,
          color: "#172033",
        },
      ],
    };
    set(
      withHistory(state, {
        deck: { ...state.deck, slides: [...state.deck.slides, slide] },
        selectedSlideId: slide.id,
        selectedElementId: slide.elements[0].id,
      })
    );
  },

  addElement: (kind) => {
    const state = get();
    const element = createElement(kind);
    const deck = {
      ...state.deck,
      slides: state.deck.slides.map((slide) =>
        slide.id === state.selectedSlideId
          ? { ...slide, elements: [...slide.elements, element] }
          : slide
      ),
    };
    set(withHistory(state, { deck, selectedElementId: element.id }));
  },

  addImageElement: (src, x = 130, y = 130) => {
    const state = get();
    const element: SlideElement = {
      ...createElement("image"),
      text: src,
      fill: "transparent",
      stroke: "transparent", // Let's set stroke to transparent for a cleaner look
      width: 420,
      height: 260,
      x,
      y,
    };
    const deck = {
      ...state.deck,
      slides: state.deck.slides.map((slide) =>
        slide.id === state.selectedSlideId
          ? { ...slide, elements: [...slide.elements, element] }
          : slide
      ),
    };
    set(withHistory(state, { deck, selectedElementId: element.id, selectedZoneKey: undefined }));
  },

  updateElement: (elementId, patch) => {
    const state = get();
    const deck = {
      ...state.deck,
      slides: state.deck.slides.map((slide) =>
        slide.id === state.selectedSlideId
          ? {
              ...slide,
              elements: slide.elements.map((element) =>
                element.id === elementId ? { ...element, ...patch } : element
              ),
            }
          : slide
      ),
    };
    set(withHistory(state, { deck }));
  },

  updateSlideZone: (slideId, zoneKey, value) => {
    const state = get();
    const deck = {
      ...state.deck,
      slides: state.deck.slides.map((slide) =>
        slide.id === slideId
          ? (() => {
              const zone_content = { ...(slide.zone_content || {}) };
              const [root, child] = zoneKey.split(".");
              if (child !== undefined) {
                const current = Array.isArray(zone_content[root]) ? [...zone_content[root]] : [];
                current[Number(child)] = value;
                zone_content[root] = current;
              } else {
                zone_content[zoneKey] = value;
              }
              return {
                ...slide,
                title: zoneKey === "title" ? String(value) : slide.title,
                zone_content,
              };
            })()
          : slide
      ),
    };
    set(withHistory(state, { deck, selectedZoneKey: zoneKey, selectedElementId: undefined }));
  },

  updateSlideZoneStyle: (slideId, zoneKey, patch) => {
    const state = get();
    const deck = {
      ...state.deck,
      slides: state.deck.slides.map((slide) => {
        if (slide.id !== slideId) return slide;
        const zone_content = slide.zone_content || {};
        const styles = zone_content.__styles || {};
        return {
          ...slide,
          zone_content: {
            ...zone_content,
            __styles: {
              ...styles,
              [zoneKey]: {
                ...(styles[zoneKey] || {}),
                ...patch,
              },
            },
          },
        };
      }),
    };
    set(withHistory(state, { deck, selectedZoneKey: zoneKey, selectedElementId: undefined }));
  },

  deleteSelectedElement: () => {
    const state = get();
    if (!state.selectedElementId) return;
    const deck = {
      ...state.deck,
      slides: state.deck.slides.map((slide) =>
        slide.id === state.selectedSlideId
          ? {
              ...slide,
              elements: slide.elements.filter((element) => element.id !== state.selectedElementId),
            }
          : slide
      ),
    };
    set(withHistory(state, { deck, selectedElementId: undefined }));
  },

  pasteElement: (element, x, y) => {
    const state = get();
    const pastedElement = {
      ...element,
      id: uid(element.kind),
      x: x !== undefined ? x : element.x + 20,
      y: y !== undefined ? y : element.y + 20,
    };
    const deck = {
      ...state.deck,
      slides: state.deck.slides.map((slide) =>
        slide.id === state.selectedSlideId
          ? { ...slide, elements: [...slide.elements, pastedElement] }
          : slide
      ),
    };
    set(withHistory(state, { deck, selectedElementId: pastedElement.id }));
  },

  addTextElementAt: (x, y) => {
    const state = get();
    const element = {
      id: uid("text"),
      kind: "text" as const,
      x,
      y,
      width: 350,
      height: 100,
      fill: "transparent",
      stroke: "transparent",
      color: "#172033",
      fontSize: 20,
      text: "",
    };
    const deck = {
      ...state.deck,
      slides: state.deck.slides.map((slide) =>
        slide.id === state.selectedSlideId
          ? { ...slide, elements: [...slide.elements, element] }
          : slide
      ),
    };
    set(withHistory(state, { deck, selectedElementId: element.id }));
  },

  updateSlideLayout: (slideId, layoutId) => {
    const state = get();
    const deck = {
      ...state.deck,
      slides: state.deck.slides.map((slide) => {
        if (slide.id !== slideId) return slide;
        
        // Grab existing bullet points or fallback to extracting from text elements
        const bullets = slide.bullet_points || 
          slide.elements
            .filter(el => el.kind === "text" && el.id !== `title-${slide.id}`)
            .map(el => el.text || "");

        const zone_content = layoutId 
          ? getZoneContentForLayout(
              layoutId, 
              slide.title, 
              bullets, 
              slide.visual_type || "none", 
              slide.visual_items || [],
              slide.zone_content
            ) 
          : slide.zone_content;

        return { 
          ...slide, 
          layout_id: layoutId,
          zone_content
        };
      }),
    };
    set(withHistory(state, { deck }));
  },

  setDeck: (deck) => {
    set({
      deck,
      selectedSlideId: deck.slides[0]?.id || "",
      selectedElementId: deck.slides[0]?.elements[0]?.id || undefined,
      selectedZoneKey: undefined,
      past: [],
      future: [],
      canUndo: false,
      canRedo: false,
    });
  },

  applyAgentChanges: (slideId, changes) => {
    const state = get();
    const deck = {
      ...state.deck,
      slides: state.deck.slides.map((slide) => {
        if (slide.id !== slideId) return slide;

        let updated = { ...slide };

        // Apply slide-level changes
        if (changes.background) updated.background = changes.background;
        if (changes.title) updated.title = changes.title;
        if (changes.layout_id) updated.layout_id = changes.layout_id as LayoutId;
        if (changes.zone_content) {
          updated.zone_content = { ...updated.zone_content, ...changes.zone_content };
        }
        if (changes.zone_styles) {
          const zone_content = updated.zone_content || {};
          const styles = zone_content.__styles || {};
          updated.zone_content = {
            ...zone_content,
            __styles: {
              ...styles,
              ...Object.fromEntries(
                Object.entries(changes.zone_styles).map(([key, patch]) => [
                  key,
                  { ...(styles[key] || {}), ...patch },
                ])
              ),
            },
          };
        }

        // Apply element-level changes
        if (changes.elements) {
          updated.elements = updated.elements.map((el) => {
            const patch = changes.elements![el.id];
            if (patch) return { ...el, ...patch };
            return el;
          });
        }

        return updated;
      }),
    };
    set(withHistory(state, { deck }));
  },

  undo: () => {
    const state = get();
    const previous = state.past[state.past.length - 1];
    if (!previous) return;
    set({
      ...previous,
      past: state.past.slice(0, -1),
      future: [snapshotOf(state), ...state.future],
      canUndo: state.past.length > 1,
      canRedo: true,
    });
  },

  redo: () => {
    const state = get();
    const next = state.future[0];
    if (!next) return;
    set({
      ...next,
      past: [...state.past, snapshotOf(state)],
      future: state.future.slice(1),
      canUndo: true,
      canRedo: state.future.length > 1,
    });
  },
}));
