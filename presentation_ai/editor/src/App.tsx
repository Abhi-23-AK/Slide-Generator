import {
  BarChart3,
  Circle,
  Download,
  FilePlus2,
  Image,
  MousePointer2,
  Redo2,
  Square,
  Table,
  Trash2,
  Type,
  Undo2,
  Workflow,
  ZoomIn,
  ZoomOut,
  LayoutGrid,
  Sparkles,
  X,
  Bot,
  Send,
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignJustify,
} from "lucide-react";
import { useMemo, useState, useRef, useEffect } from "react";
import type React from "react";
import { useEditorStore, mapBackendDeckToReact } from "./store/editorStore";
import type { ElementKind, SlideElement, LayoutId, Slide, AgentMessage } from "./types";
import { SlideRenderer } from "./layouts/SlideRenderer";
import { useSpeechRecognition } from "./hooks/useSpeechRecognition";
import TranslateModal from "./components/TranslateModal";

const BACKEND_URL = `http://${window.location.hostname}:8000`;

const SLIDE_WIDTH = 1120;
const SLIDE_HEIGHT = 630;
const FRAME_WIDTH = 1920;
const FRAME_HEIGHT = 1080;
const FRAME_X_SCALE = FRAME_WIDTH / SLIDE_WIDTH;
const FRAME_Y_SCALE = FRAME_HEIGHT / SLIDE_HEIGHT;

const elementTools: Array<{ kind: ElementKind; label: string; icon: React.ComponentType<{ size?: number }> }> = [
  { kind: "text", label: "Text", icon: Type },
  { kind: "shape", label: "Shape", icon: Square },
  { kind: "icon", label: "Icons", icon: Circle },
  { kind: "image", label: "Image", icon: Image },
  { kind: "flow", label: "Flow", icon: Workflow },
  { kind: "chart", label: "Chart", icon: BarChart3 },
  { kind: "table", label: "Table", icon: Table },
];

export function App() {
  const {
    deck,
    selectedSlideId,
    selectedElementId,
    selectedZoneKey,
    zoom,
    canUndo,
    canRedo,
    selectSlide,
    selectElement,
    setZoom,
    addSlide,
    addElement,
    addImageElement,
    deleteSelectedElement,
    updateSlideLayout,
    undo,
    redo,
    setDeck,
    applyAgentChanges,
    pasteElement,
    addTextElementAt,
  } = useEditorStore();

  const [isGenModalOpen, setIsGenModalOpen] = useState(false);
  const [genMode, setGenMode] = useState<"topic" | "prompt">("topic");
  const [genTopic, setGenTopic] = useState("");
  const [currentTopic, setCurrentTopic] = useState("");
  const [genCount, setGenCount] = useState(5);
  const [genTone, setGenTone] = useState("Professional");
  const [genTitles, setGenTitles] = useState("");
  const [genFile, setGenFile] = useState<File | null>(null);
  const [genTemplateFile, setGenTemplateFile] = useState<File | null>(null);
  const [templateMode, setTemplateMode] = useState(false);
  const [templateSlideCount, setTemplateSlideCount] = useState<number | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [genError, setGenError] = useState("");
  const [genStatus, setGenStatus] = useState("");
  const [promptSlides, setPromptSlides] = useState<Array<{ title: string; content: string }>>([]);

  const [isAgentOpen, setIsAgentOpen] = useState(false);
  const [agentMessages, setAgentMessages] = useState<AgentMessage[]>([]);
  const [agentInput, setAgentInput] = useState("");
  const [baseInput, setBaseInput] = useState("");
  const [isAgentLoading, setIsAgentLoading] = useState(false);
  const [agentError, setAgentError] = useState<string | null>(null);

  const [translateModalOpen, setTranslateModalOpen] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [templateSessionId, setTemplateSessionId] = useState<string | null>(null);
  const [pptxReady, setPptxReady] = useState(false);
  const [pptxStatus, setPptxStatus] = useState<"idle" | "building" | "ready" | "failed">("idle");
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [youtubeStatus, setYoutubeStatus] = useState<"idle" | "extracting" | "summarizing" | "ready" | "error">("idle");
  const [youtubeError, setYoutubeError] = useState("");
  const [architectureType, setArchitectureType] = useState("none");
  const [architectureStyle, setArchitectureStyle] = useState("classic");

  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    elementId: string;
  } | null>(null);
  const [clipboardElement, setClipboardElement] = useState<SlideElement | null>(null);
  const [lastClickCoords, setLastClickCoords] = useState<{ x: number; y: number } | null>(null);

  const ignoreDeckChangeRef = useRef(false);

  // Reset pptxReady and sessionId on deck changes (edits), unless it's the initial deck generation
  useEffect(() => {
    if (ignoreDeckChangeRef.current) {
      ignoreDeckChangeRef.current = false;
      return;
    }
    if (!templateMode) {
      setPptxReady(false);
      setSessionId(null);
      setPptxStatus("idle");
    }
  }, [deck, templateMode]);

  // Reset YouTube generation states when modal is closed
  useEffect(() => {
    if (!isGenModalOpen) {
      setYoutubeUrl("");
      setYoutubeStatus("idle");
      setYoutubeError("");
    }
  }, [isGenModalOpen]);

  const { 
    transcript, 
    isListening, 
    startListening, 
    stopListening, 
    isSupported: isSpeechSupported,
    error: speechError,
    resetTranscript,
  } = useSpeechRecognition();

  // Auto-fill input when speech is recognized
  useEffect(() => {
    if (transcript) {
      setAgentInput(baseInput + transcript);
    }
  }, [transcript, baseInput]);

  // When listening stops, commit the transcript to baseInput and reset speech transcript
  useEffect(() => {
    if (!isListening && transcript) {
      const finalVal = baseInput + transcript;
      setBaseInput(finalVal);
      setAgentInput(finalVal);
      resetTranscript();
    }
  }, [isListening, transcript, baseInput, resetTranscript]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isAgentOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [agentMessages, isAgentLoading, isAgentOpen]);

  // Poll for PPTX build status when sessionId changes
  useEffect(() => {
    if (!sessionId) return;

    setPptxStatus("building");
    const poll = setInterval(async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/pptx-status/${sessionId}`);
        const data = await res.json();
        if (data.ready) {
          setPptxReady(true);
          setPptxStatus("ready");
          clearInterval(poll);
        } else if (data.status === "failed") {
          console.error("PPTX background pre-build failed.");
          setPptxReady(false);
          setPptxStatus("failed");
          clearInterval(poll);
        }
      } catch (err) {
        console.error("Failed to check PPTX status:", err);
      }
    }, 3000);  // check every 3 seconds

    return () => clearInterval(poll);
  }, [sessionId]);

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      const topicName = currentTopic.trim() ? currentTopic.trim() : (deck.title || "presentation");
      
      if (templateMode) {
        if (pptxReady && sessionId) {
          window.location.href = `${BACKEND_URL}/download-pptx/${sessionId}`;
        } else {
          alert("Your PPTX is still building in the background. Please wait a moment.");
        }
      } else {
        // Standard mode fallback
        if (pptxReady && sessionId) {
          window.location.href = `${BACKEND_URL}/download-pptx/${sessionId}`;
        } else {
          const response = await fetch(`${BACKEND_URL}/export-pptx`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              ...deck,
              session_id: sessionId,
              template_mode: templateMode,
              tone: genTone,
              topic: topicName,
            }),
          });
          if (!response.ok) {
            throw new Error("Failed to export PPTX");
          }
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          const safeTopicName = topicName.replace(/[/\\?%*:|"<>. ]/g, "_");
          a.download = `${safeTopicName}.pptx`;
          document.body.appendChild(a);
          a.click();
          a.remove();
        }
      }
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setIsDownloading(false);
    }
  };

  const handleExtractAndSummarize = async () => {
    if (!youtubeUrl.trim()) {
      setYoutubeError("Please enter a valid YouTube video URL.");
      setYoutubeStatus("error");
      return;
    }

    setYoutubeError("");
    setYoutubeStatus("extracting");

    // Simulate transition to summarizing after 2 seconds
    const timer = setTimeout(() => {
      setYoutubeStatus("summarizing");
    }, 2000);

    try {
      const formData = new FormData();
      formData.append("url", youtubeUrl.trim());

      const response = await fetch(`${BACKEND_URL}/video/summarize`, {
        method: "POST",
        body: formData,
      });

      clearTimeout(timer);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to extract and summarize video.");
      }

      await response.json();
      setYoutubeStatus("ready");
    } catch (err: any) {
      clearTimeout(timer);
      setYoutubeError(err.message || "An error occurred.");
      setYoutubeStatus("error");
    }
  };

  const closeGenModal = () => {
    setIsGenModalOpen(false);
    setArchitectureType("none");
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (genMode === "topic") {
      if (!genTopic.trim()) {
        setGenError("Topic is required.");
        return;
      }
      
      setCurrentTopic(genTopic.trim());
      setIsGenerating(true);
      setGenError("");
      setGenStatus("Connecting to AI outline planner...");
      
      try {
        const formData = new FormData();
        formData.append("topic", genTopic);
        formData.append("slide_count", genCount.toString());
        formData.append("tone", genTone);
        if (genTitles.trim()) {
          formData.append("sample_titles", genTitles);
        }
        if (genFile) {
          formData.append("pdf_file", genFile);
        }
        if (genTemplateFile) {
          formData.append("template_file", genTemplateFile);
        }
        if (youtubeUrl.trim()) {
          formData.append("youtube_url", youtubeUrl.trim());
        }
        formData.append("architecture_type", architectureType);
        formData.append("architecture_style", architectureStyle);
        
        setGenStatus("AI is generating outlines and checking layouts...");
        
        const response = await fetch(`${BACKEND_URL}/generate-json`, {
          method: "POST",
          body: formData,
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Failed to generate presentation.");
        }
        
        setGenStatus("Compiling presentation layouts and elements...");
        const backendDeck = await response.json();
        
        // Capture session_id for background PPTX build
        if (backendDeck.session_id) {
          setSessionId(backendDeck.session_id);
          setPptxReady(false);
          if (backendDeck.template_mode) {
            setTemplateSessionId(backendDeck.session_id);
          } else {
            setTemplateSessionId(null);
          }
        }
        
        if (backendDeck.template_mode) {
          setTemplateMode(true);
          setTemplateSlideCount(backendDeck.template_slide_count);
        } else {
          setTemplateMode(false);
          setTemplateSlideCount(null);
        }
        
        const mappedDeck = mapBackendDeckToReact(backendDeck, genTone);
        
        ignoreDeckChangeRef.current = true;
        setDeck(mappedDeck);
        setIsGenModalOpen(false);
        
        // Reset form
        setGenTopic("");
        setGenFile(null);
        setGenTemplateFile(null);
        setGenCount(5);
        setYoutubeUrl("");
        setYoutubeStatus("idle");
        setYoutubeError("");
        setArchitectureType("none");
      } catch (err: any) {
        setGenError(err.message || "An error occurred.");
      } finally {
        setIsGenerating(false);
        setGenStatus("");
      }
    } else {
      // Prompt mode
      if (promptSlides.length === 0) {
        setGenError("Please add at least one slide.");
        return;
      }
      
      setCurrentTopic("Custom Prompts");
      setIsGenerating(true);
      setGenError("");
      setGenStatus("Generating presentation from custom prompts...");
      
      try {
        const response = await fetch(`${BACKEND_URL}/generate-from-prompts`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            tone: genTone,
            slides: promptSlides,
          }),
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Failed to generate presentation.");
        }
        
        setGenStatus("Compiling presentation layouts and elements...");
        const backendDeck = await response.json();
        
        // Capture session_id for background PPTX build
        if (backendDeck.session_id) {
          setSessionId(backendDeck.session_id);
          setPptxReady(false);
        }
        
        const mappedDeck = mapBackendDeckToReact(backendDeck, genTone);
        
        ignoreDeckChangeRef.current = true;
        setDeck(mappedDeck);
        setIsGenModalOpen(false);
        
        // Reset form
        setPromptSlides([]);
        setArchitectureType("none");
      } catch (err: any) {
        setGenError(err.message || "An error occurred.");
      } finally {
        setIsGenerating(false);
        setGenStatus("");
      }
    }
  };

  const handleSendAgentMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!agentInput.trim() || isAgentLoading || !slide) return;

    const userText = agentInput.trim();
    setAgentInput("");
    setBaseInput("");
    setAgentError(null);

    const userMsg: AgentMessage = {
      id: `msg-${Date.now()}-user`,
      role: "user",
      text: userText,
      timestamp: Date.now(),
    };

    setAgentMessages((prev) => [...prev, userMsg]);
    setIsAgentLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/agent-edit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          slide,
          selectedElementId,
          selectedZoneKey,
          instruction: userText,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to make changes.");
      }

      const result = await response.json();
      applyAgentChanges(slide.id, result.changes);

      const aiMsg: AgentMessage = {
        id: `msg-${Date.now()}-ai`,
        role: "ai",
        text: result.message || "Changes applied successfully.",
        timestamp: Date.now(),
      };

      setAgentMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const errorMsg: AgentMessage = {
        id: `msg-${Date.now()}-error`,
        role: "ai",
        text: `⚠️ Error: ${err.message || "Something went wrong."}`,
        timestamp: Date.now(),
      };
      setAgentMessages((prev) => [...prev, errorMsg]);
      setAgentError(err.message || "Something went wrong.");
    } finally {
      setIsAgentLoading(false);
    }
  };

  const handleChipClick = (text: string) => {
    setAgentInput(text);
    setBaseInput(text);
    inputRef.current?.focus();
  };

  const handleCutElement = (elementId: string) => {
    const elementToCut = slide?.elements.find((el) => el.id === elementId);
    if (elementToCut) {
      setClipboardElement(elementToCut);
      selectElement(elementId);
      deleteSelectedElement();
    }
    setContextMenu(null);
  };

  const handleDeleteElement = (elementId: string) => {
    selectElement(elementId);
    deleteSelectedElement();
    setContextMenu(null);
  };

  const slide = useMemo(
    () => deck.slides.find((item) => item.id === selectedSlideId) ?? deck.slides[0],
    [deck.slides, selectedSlideId]
  );
  const selectedElement = slide ? slide.elements.find((element) => element.id === selectedElementId) : undefined;

  useEffect(() => {
    const handlePaste = (event: ClipboardEvent) => {
      if (!slide) return;

      const imageItem = Array.from(event.clipboardData?.items || []).find((item) => item.type.startsWith("image/"));
      
      // Handle image pasting first, regardless of active elements (e.g. focused textarea)
      if (imageItem) {
        const file = imageItem.getAsFile();
        if (!file) return;
        event.preventDefault();

        const reader = new FileReader();
        reader.onload = () => {
          if (typeof reader.result === "string") {
            const targetX = lastClickCoords?.x ?? 130;
            const targetY = lastClickCoords?.y ?? 130;
            if (selectedElement && selectedElement.kind === "text" && !selectedElement.text) {
              deleteSelectedElement();
            }
            addImageElement(reader.result, targetX, targetY);
          }
        };
        reader.readAsDataURL(file);
        return;
      }

      // For non-image pastes, if a text editor is active, let the browser handle it naturally
      const active = document.activeElement;
      if (active instanceof HTMLElement && (active.isContentEditable || active.tagName === "TEXTAREA")) return;

      if (clipboardElement) {
        event.preventDefault();
        const targetX = lastClickCoords?.x ?? clipboardElement.x + 20;
        const targetY = lastClickCoords?.y ?? clipboardElement.y + 20;
        if (selectedElement && selectedElement.kind === "text" && !selectedElement.text) {
          deleteSelectedElement();
        }
        pasteElement(clipboardElement, targetX, targetY);
        return;
      }
    };

    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  }, [addImageElement, slide, clipboardElement, pasteElement, lastClickCoords, selectedElement, deleteSelectedElement]);

  useEffect(() => {
    const closeMenu = () => setContextMenu(null);
    window.addEventListener("click", closeMenu);
    return () => window.removeEventListener("click", closeMenu);
  }, []);


  return (
    <div className="editor-shell">
      <header className="topbar">
        <div className="brand">
          <MousePointer2 size={18} />
          <span>Slide Editor</span>
          {templateMode && templateSlideCount !== null && (
            <span style={{
              marginLeft: 12,
              fontSize: 11,
              fontWeight: 600,
              color: "#4f46e5",
              background: "#eef2ff",
              padding: "2px 8px",
              borderRadius: 12,
              border: "1px solid #c7d2fe",
              display: "inline-flex",
              alignItems: "center",
              gap: 4
            }}>
              <span>📎</span>
              <span>Template Mode ({templateSlideCount} slides)</span>
            </span>
          )}
        </div>
        <div className="toolbar" aria-label="Editor tools">
          <IconButton label="Undo" icon={Undo2} onClick={undo} disabled={!canUndo} />
          <IconButton label="Redo" icon={Redo2} onClick={redo} disabled={!canRedo} />
          <div className="separator" />
          {elementTools.map((tool) => (
            <IconButton
              key={tool.kind}
              label={tool.label}
              icon={tool.icon}
              onClick={() => addElement(tool.kind)}
            />
          ))}
          <div className="separator" />
          <IconButton label="Zoom out" icon={ZoomOut} onClick={() => setZoom(Math.max(0.35, zoom - 0.08))} />
          <span className="zoom-label">{Math.round(zoom * 100)}%</span>
          <IconButton label="Zoom in" icon={ZoomIn} onClick={() => setZoom(Math.min(1.25, zoom + 0.08))} />
          <div className="separator" />
          <IconButton label="Delete" icon={Trash2} onClick={deleteSelectedElement} disabled={!selectedElement} />
          <IconButton 
            label={
              isDownloading 
                ? "Downloading..." 
                : templateMode
                  ? pptxReady
                    ? "Download PPTX Presentation"
                    : pptxStatus === "failed"
                      ? "❌ Build Failed"
                      : "⏳ Building PPTX..."
                  : (sessionId && !pptxReady)
                    ? "⏳ Building PPTX..." 
                    : "Download PPTX Presentation"
            } 
            icon={Download} 
            onClick={handleDownload} 
            disabled={isDownloading || (templateMode && !pptxReady) || (!templateMode && !!sessionId && !pptxReady)} 
          />
          <div className="separator" />
          <button
            onClick={() => setTranslateModalOpen(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              background: 'white',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: '600',
              color: '#334155',
              height: '32px',
              boxSizing: 'border-box',
              transition: 'background 0.2s, border-color 0.2s'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = '#f1f5f9';
              e.currentTarget.style.borderColor = '#94a3b8';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'white';
              e.currentTarget.style.borderColor = '#cbd5e1';
            }}
          >
            <span>🌐 Translate</span>
          </button>
        </div>
      </header>

      <aside className="slide-rail">
        <button className="new-slide" onClick={addSlide}>
          <FilePlus2 size={16} />
          <span>Slide</span>
        </button>
        <button className="ai-generate-button" onClick={() => setIsGenModalOpen(true)}>
          <Sparkles size={16} />
          <span>AI Generate</span>
        </button>
        <button className="agent-trigger-button" onClick={() => setIsAgentOpen((prev) => !prev)}>
          <Bot size={16} />
          <span>Make Changes with Agent</span>
        </button>

        <div className="thumb-list">
          {deck.slides.map((item, index) => (
            <button
              key={item.id}
              className={`thumb ${item.id === selectedSlideId ? "selected" : ""}`}
              onClick={() => selectSlide(item.id)}
            >
              <span className="thumb-index">{index + 1}</span>
              <span className="thumb-title">{item.title}</span>
            </button>
          ))}
        </div>
      </aside>

      <main className="workspace">
        {!slide ? (
          <div className="empty-workspace-state" style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100%",
            color: "#64748b",
            gap: "12px"
          }}>
            <LayoutGrid size={48} strokeWidth={1} />
            <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 600 }}>No Slides in Deck</h3>
            <p style={{ margin: 0, fontSize: "13px" }}>Click "+ Slide" or "AI Generate" to get started.</p>
          </div>
        ) : (
          <>
            <div className="canvas-header" style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "12px 24px",
              background: "#ffffff",
              borderBottom: "1px solid #cfd6e3",
            }}>
              <div className="slide-meta" style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <h2 style={{ margin: 0, fontSize: "14px", fontWeight: 700 }}>Slide: {slide.title}</h2>
                {slide.layout_id ? (
                  <span className="layout-badge" style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                    fontSize: "11px",
                    fontWeight: 700,
                    color: "#2563eb",
                    background: "#eff6ff",
                    padding: "3px 8px",
                    borderRadius: "12px",
                    border: "1px solid #bfdbfe"
                  }}>
                    <LayoutGrid size={12} />
                    {slide.layout_id} Layout
                    {slide.layout_score !== undefined && (
                      <span style={{ color: "#64748b", fontWeight: 500 }}>({Math.round(slide.layout_score * 100)}%)</span>
                    )}
                  </span>
                ) : (
                  <span className="layout-badge none" style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    color: "#64748b",
                    background: "#f1f5f9",
                    padding: "3px 8px",
                    borderRadius: "12px",
                  }}>
                    No Layout
                  </span>
                )}
              </div>
              
              <div className="layout-override" style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px" }}>
                <label htmlFor="layout-select" style={{ fontWeight: 600, color: "#475569" }}>Layout Override:</label>
                <select
                  id="layout-select"
                  value={slide.layout_id || ""}
                  onChange={(e) => {
                    const val = e.target.value;
                    updateSlideLayout(slide.id, val ? (val as LayoutId) : undefined);
                  }}
                  style={{
                    height: "28px",
                    borderRadius: "4px",
                    border: "1px solid #cad7e8",
                    background: "#ffffff",
                    padding: "0 6px",
                    fontWeight: 500
                  }}
                >
                  <option value="">None (Generic Canvas)</option>
                  <option value="OneColumn">OneColumn</option>
                  <option value="TwoColumn">TwoColumn</option>
                  <option value="ThreeColumn">ThreeColumn</option>
                  <option value="FourGrid">FourGrid</option>
                  <option value="Hero">Hero</option>
                  <option value="Dashboard">Dashboard</option>
                  <option value="Architecture">Architecture</option>
                  <option value="Timeline">Timeline</option>
                  <option value="Comparison">Comparison</option>
                  <option value="Process">Process</option>
                </select>
              </div>
            </div>

            <div className="canvas-stage">
              {slide.layout_id ? (
                <SlideRenderer
                  slide={slide}
                  slideNumber={deck.slides.indexOf(slide) + 1}
                  totalSlides={deck.slides.length}
                  theme={deck.theme}
                  zoom={zoom}
                  editing
                  editingChildren={
                    slide.elements.length > 0 ? (
                      <div className="template-object-layer" onClick={() => selectElement(undefined)}>
                        {slide.elements.map((element) => (
                          <SlideObject
                            key={element.id}
                            element={element}
                            selected={element.id === selectedElementId}
                            coordinateScaleX={FRAME_X_SCALE}
                            coordinateScaleY={FRAME_Y_SCALE}
                            onContextMenu={(x, y, elementId) => setContextMenu({ x, y, elementId })}
                          />
                        ))}
                      </div>
                    ) : undefined
                  }
                />
              ) : (
                <div
                  className="slide-scale-wrapper"
                  style={{
                    width: SLIDE_WIDTH * zoom,
                    height: SLIDE_HEIGHT * zoom,
                    position: "relative",
                    flexShrink: 0,
                  }}
                >
                  <div
                    className="slide-canvas"
                    style={{
                      width: SLIDE_WIDTH,
                      height: SLIDE_HEIGHT,
                      transform: `scale(${zoom})`,
                      transformOrigin: "0 0",
                      position: "absolute",
                      left: 0,
                      top: 0,
                      background: slide.background,
                    }}
                    onClick={(e) => {
                      if (e.target !== e.currentTarget) return; // Only if clicking directly on canvas background
                      const rect = e.currentTarget.getBoundingClientRect();
                      const clickX = Math.round((e.clientX - rect.left) / zoom);
                      const clickY = Math.round((e.clientY - rect.top) / zoom);
                      addTextElementAt(clickX, clickY);
                    }}
                  >
                    {slide.elements.map((element) => (
                      <SlideObject
                        key={element.id}
                        element={element}
                        selected={element.id === selectedElementId}
                        onContextMenu={(x, y, elementId) => setContextMenu({ x, y, elementId })}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </main>

      <aside className="inspector">
        {slide ? (
          <Inspector element={selectedElement} slide={slide} selectedZoneKey={selectedZoneKey} />
        ) : (
          <div className="panel slide-inspector">
            <h2>Slide Settings</h2>
            <div style={{ marginTop: "20px", fontSize: "12px", color: "#64748b" }}>
              No slide selected.
            </div>
          </div>
        )}
      </aside>


      {isGenModalOpen && (
        <div className="modal-overlay" onClick={() => !isGenerating && closeGenModal()}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <Sparkles size={18} style={{ color: "#6366f1" }} />
              <h3>Generate Presentation with AI</h3>
              <button 
                className="icon-button" 
                style={{ marginLeft: "auto" }} 
                onClick={closeGenModal}
                disabled={isGenerating}
              >
                <X size={16} />
              </button>
            </div>
            
            {isGenerating ? (
              <div className="loading-state">
                <div className="spinner"></div>
                <div className="loading-message">{genStatus}</div>
              </div>
            ) : (
              <form onSubmit={handleGenerate}>
                <div className="modal-body" style={{ maxHeight: "60vh", overflowY: "auto" }}>
                  {genError && (
                    <div className="error-banner">
                      <span>⚠️</span>
                      <span>{genError}</span>
                    </div>
                  )}
                  
                  {/* Mode Toggle */}
                  <div className="form-group">
                    <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
                      <button
                        type="button"
                        className={`btn ${genMode === "topic" ? "btn-primary" : "btn-secondary"}`}
                        onClick={() => setGenMode("topic")}
                        style={{ flex: 1 }}
                      >
                        📝 Topic Mode
                      </button>
                      <button
                        type="button"
                        className={`btn ${genMode === "prompt" ? "btn-primary" : "btn-secondary"}`}
                        onClick={() => setGenMode("prompt")}
                        style={{ flex: 1 }}
                      >
                        💬 Prompt Mode
                      </button>
                    </div>
                  </div>

                  {genMode === "topic" ? (
                    <>
                      <div className="form-group">
                        <label htmlFor="modal-topic">What is the topic of your presentation?</label>
                        <input
                          id="modal-topic"
                          type="text"
                          placeholder="e.g. History of Space Exploration or React Hooks Guide"
                          value={genTopic}
                          onChange={(e) => setGenTopic(e.target.value)}
                          required
                        />
                      </div>

                      <div className="form-group" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                        <div>
                          <label htmlFor="modal-count">Slide Count</label>
                          <select
                            id="modal-count"
                            value={genCount}
                            onChange={(e) => setGenCount(Number(e.target.value))}
                            disabled={!!genTemplateFile}
                          >
                            {genTemplateFile ? (
                              <option value={0}>Matches Template</option>
                            ) : (
                              [3, 4, 5, 6, 7, 8, 9, 10, 12, 15].map((num) => (
                                <option key={num} value={num}>{num} slides</option>
                              ))
                            )}
                          </select>
                        </div>
                        <div>
                          <label htmlFor="modal-tone">Tone</label>
                          <select
                            id="modal-tone"
                            value={genTone}
                            onChange={(e) => setGenTone(e.target.value)}
                            disabled={!!genTemplateFile}
                          >
                            <option value="Professional">Professional</option>
                            <option value="Lavish">Lavish</option>
                            <option value="Creative">Creative</option>
                            <option value="Technical">Technical</option>
                            <option value="Academic">Academic</option>
                            <option value="Education">Education</option>
                            <option value="Ecommerce">E-Commerce</option>
                            <option value="Neumorphism">Neumorphism</option>
                          </select>
                        </div>
                      </div>

                      <div className="form-group">
                        <label htmlFor="modal-titles">Sample Slide Titles (Optional, comma separated)</label>
                        <input
                          id="modal-titles"
                          type="text"
                          placeholder="e.g. Introduction, Core Problems, Proposed Solution"
                          value={genTitles}
                          onChange={(e) => setGenTitles(e.target.value)}
                        />
                      </div>

                      <div className="form-group">
                        <label htmlFor="modal-file">Upload Source Document (Optional PDF / DOCX / TXT)</label>
                        <input
                          id="modal-file"
                          type="file"
                          accept=".pdf,.docx,.txt"
                          onChange={(e) => setGenFile(e.target.files?.[0] || null)}
                        />
                      </div>

                      <div className="form-group" style={{ borderTop: "1px solid #e2e8f0", paddingTop: "16px", marginTop: "16px" }}>
                        <label htmlFor="modal-youtube">YouTube Video URL (Optional)</label>
                        <div style={{ display: "flex", gap: "8px" }}>
                          <input
                            id="modal-youtube"
                            type="text"
                            placeholder="https://www.youtube.com/watch?v=..."
                            value={youtubeUrl}
                            onChange={(e) => {
                              setYoutubeUrl(e.target.value);
                              if (youtubeStatus !== "idle") {
                                setYoutubeStatus("idle");
                                setYoutubeError("");
                              }
                            }}
                            disabled={youtubeStatus === "extracting" || youtubeStatus === "summarizing"}
                            style={{ flex: 1 }}
                          />
                          <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={handleExtractAndSummarize}
                            disabled={!youtubeUrl.trim() || youtubeStatus === "extracting" || youtubeStatus === "summarizing"}
                            style={{ whiteSpace: "nowrap" }}
                          >
                            {youtubeStatus === "extracting" || youtubeStatus === "summarizing" ? "Processing..." : "Extract & Summarize"}
                          </button>
                        </div>

                        {youtubeStatus === 'extracting' && (
                          <div style={{ marginTop: 8, fontSize: 13, color: "#6366f1", display: "flex", alignItems: "center", gap: 6 }}>
                            <div style={{
                              width: "14px",
                              height: "14px",
                              border: "2px solid #f3f3f3",
                              borderTop: "2px solid #6366f1",
                              borderRadius: "50%",
                              animation: "spin 1s linear infinite"
                            }}></div>
                            <span>Extracting transcript...</span>
                          </div>
                        )}
                        {youtubeStatus === 'summarizing' && (
                          <div style={{ marginTop: 8, fontSize: 13, display: "flex", flexDirection: "column", gap: 4 }}>
                            <div style={{ color: "#22c55e", display: "flex", alignItems: "center", gap: 6 }}>
                              <span>✓</span> <span>Transcript extracted</span>
                            </div>
                            <div style={{ color: "#6366f1", display: "flex", alignItems: "center", gap: 6 }}>
                              <div style={{
                                width: "14px",
                                height: "14px",
                                border: "2px solid #f3f3f3",
                                borderTop: "2px solid #6366f1",
                                borderRadius: "50%",
                                animation: "spin 1s linear infinite"
                              }}></div>
                              <span>Summarizing transcript...</span>
                            </div>
                          </div>
                        )}
                        {youtubeStatus === 'ready' && (
                          <div style={{ marginTop: 8, fontSize: 13, display: "flex", flexDirection: "column", gap: 4 }}>
                            <div style={{ color: "#22c55e", display: "flex", alignItems: "center", gap: 6 }}>
                              <span>✓</span> <span>Transcript extracted</span>
                            </div>
                            <div style={{ color: "#22c55e", display: "flex", alignItems: "center", gap: 6 }}>
                              <span>✓</span> <span>Summary generated</span>
                            </div>
                            <div style={{ color: "#22c55e", display: "flex", alignItems: "center", gap: 6 }}>
                              <span>✓</span> <span>Ready for presentation</span>
                            </div>
                          </div>
                        )}
                        {youtubeStatus === 'error' && youtubeError && (
                          <div style={{ marginTop: 8, fontSize: 13, color: "#ef4444", display: "flex", alignItems: "center", gap: 6 }}>
                            <span>⚠️</span> <span>{youtubeError}</span>
                          </div>
                        )}
                      </div>

                      <div className="form-group">
                        <label htmlFor="modal-template">Upload PowerPoint Template (Optional .pptx)</label>
                        <input
                          id="modal-template"
                          type="file"
                          accept=".pptx"
                           onChange={(e) => {
                            const file = e.target.files?.[0] || null;
                            setGenTemplateFile(file);
                            if (file) {
                              setGenCount(0);
                              setGenTone("Professional");
                            } else {
                              setGenCount(5);
                            }
                          }}
                        />
                        {genTemplateFile && (
                          <div style={{ marginTop: 6, fontSize: 12, color: "#22c55e", display: "flex", alignItems: "center", gap: 6 }}>
                            <span>✅</span>
                            <span>{genTemplateFile.name} — slide count will match template</span>
                          </div>
                        )}
                      </div>

                      <div className="form-group">
                        <label htmlFor="modal-architecture-type">Architecture Diagram Type</label>
                        <select
                          id="modal-architecture-type"
                          value={architectureType}
                          onChange={(e) => setArchitectureType(e.target.value)}
                        >
                          <option value="none">none</option>
                          <option value="auto">auto</option>
                          <option value="layered">layered</option>
                          <option value="microservices">microservices</option>
                          <option value="cloud">cloud</option>
                          <option value="event_driven">event_driven</option>
                          <option value="star">star</option>
                          <option value="ring">ring</option>
                          <option value="hub_spoke">hub_spoke</option>
                          <option value="kubernetes">kubernetes</option>
                          <option value="ai_pipeline">ai_pipeline</option>
                          <option value="transformer">transformer</option>
                          <option value="cnn">cnn</option>
                          <option value="uml">uml</option>
                          <option value="flowchart">flowchart</option>
                        </select>
                      </div>

                      <div className="form-group">
                        <label htmlFor="modal-architecture-style">Architecture Visual Style</label>
                        <select
                          id="modal-architecture-style"
                          value={architectureStyle}
                          onChange={(e) => setArchitectureStyle(e.target.value)}
                        >
                          <option value="classic">Classic (Pastel)</option>
                          <option value="aiicons">AI Dark Neon</option>
                          <option value="aws_icons">AWS Theme</option>
                          <option value="azure_icons">Azure Theme</option>
                          <option value="gcp_icons">GCP Theme</option>
                          <option value="k8s_icons">Kubernetes Theme</option>
                          <option value="drawio_skill">DrawIO Vivid</option>
                          <option value="minimal">Minimal (Monochrome)</option>
                        </select>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="form-group">
                        <label htmlFor="modal-tone-prompt">Tone</label>
                        <select
                          id="modal-tone-prompt"
                          value={genTone}
                          onChange={(e) => setGenTone(e.target.value)}
                        >
                          <option value="Professional">Professional</option>
                          <option value="Lavish">Lavish</option>
                          <option value="Creative">Creative</option>
                          <option value="Technical">Technical</option>
                          <option value="Academic">Academic</option>
                          <option value="Education">Education</option>
                          <option value="Ecommerce">E-Commerce</option>
                          <option value="Neumorphism">Neumorphism</option>
                        </select>
                      </div>

                      <div className="form-group">
                        <label>Slide Count: {promptSlides.length}</label>
                        <div style={{ display: "flex", gap: "8px", marginTop: "8px" }}>
                          <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={() => setPromptSlides([...promptSlides, { title: "", content: "" }])}
                          >
                            + Add Slide
                          </button>
                          {promptSlides.length > 0 && (
                            <button
                              type="button"
                              className="btn btn-secondary"
                              onClick={() => setPromptSlides(promptSlides.slice(0, -1))}
                            >
                              - Remove Last
                            </button>
                          )}
                        </div>
                      </div>

                      {promptSlides.map((slide, index) => (
                        <div key={index} className="form-group" style={{
                          background: "#f8fafc",
                          padding: "16px",
                          borderRadius: "8px",
                          border: "1px solid #e2e8f0"
                        }}>
                          <label htmlFor={`prompt-slide-title-${index}`}>Slide {index + 1} Title</label>
                          <input
                            id={`prompt-slide-title-${index}`}
                            type="text"
                            placeholder="Enter slide title"
                            value={slide.title}
                            onChange={(e) => {
                              const newSlides = [...promptSlides];
                              newSlides[index].title = e.target.value;
                              setPromptSlides(newSlides);
                            }}
                            style={{ marginBottom: "8px" }}
                          />
                          <label htmlFor={`prompt-slide-content-${index}`}>Slide {index + 1} Content / Instructions</label>
                          <textarea
                            id={`prompt-slide-content-${index}`}
                            placeholder="Enter the content or instructions for this slide"
                            value={slide.content}
                            onChange={(e) => {
                              const newSlides = [...promptSlides];
                              newSlides[index].content = e.target.value;
                              setPromptSlides(newSlides);
                            }}
                            rows={3}
                            style={{
                              width: "100%",
                              padding: "8px",
                              border: "1px solid #cbd5e1",
                              borderRadius: "4px",
                              fontSize: "13px",
                              fontFamily: "inherit",
                              resize: "vertical"
                            }}
                          />
                        </div>
                      ))}
                    </>
                  )}
                </div>
                
                <div className="modal-footer">
                  <button 
                    type="button" 
                    className="btn btn-secondary" 
                    onClick={closeGenModal}
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    className="btn btn-primary"
                  >
                    Generate Deck
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      <TranslateModal
        isOpen={translateModalOpen}
        onClose={() => setTranslateModalOpen(false)}
        deck={deck}
        onTranslated={(translated) => {
          setDeck(translated);
          setTranslateModalOpen(false);
        }}
      />

      {isAgentOpen && (
        <div className="agent-chatbot">
          <div className="agent-header">
            <div className="agent-header-icon">
              <Bot size={18} />
            </div>
            <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
              <div className="agent-header-title">AI Design Partner</div>
              <div className="agent-header-subtitle">Real-time slide editor</div>
            </div>
            <button className="agent-close-btn" onClick={() => setIsAgentOpen(false)}>
              <X size={16} />
            </button>
          </div>

          <div className="agent-slide-context">
            <span>Editing:</span>
            {slide ? (
              <span className="agent-slide-context-badge">
                Slide {deck.slides.indexOf(slide) + 1}: {slide.title}
              </span>
            ) : (
              <span className="agent-slide-context-badge">No slide selected</span>
            )}
          </div>

          <div className="agent-messages">
            {agentMessages.length === 0 ? (
              <div className="agent-welcome">
                <div className="agent-welcome-icon">
                  <Bot size={24} />
                </div>
                <p style={{ margin: 0, fontWeight: 700, color: "#475569", marginBottom: "6px" }}>
                  How can I help you design?
                </p>
                <p style={{ margin: 0, fontSize: "12px", color: "#64748b" }}>
                  Ask me to change backgrounds, modify text, alter colors, update sizes, or apply a different layout.
                </p>
              </div>
            ) : (
              agentMessages.map((msg) => (
                <div
                  key={msg.id}
                  className={`agent-msg ${
                    msg.role === "user"
                      ? "agent-msg-user"
                      : msg.text.startsWith("⚠️")
                      ? "agent-msg-error"
                      : "agent-msg-ai"
                  }`}
                >
                  <div>{msg.text}</div>
                  <div className="agent-msg-time">
                    {new Date(msg.timestamp).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
              ))
            )}
            {isAgentLoading && (
              <div className="agent-typing">
                <div className="agent-typing-dot" />
                <div className="agent-typing-dot" />
                <div className="agent-typing-dot" />
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="agent-chips">
            <button
              className="agent-chip"
              onClick={() => handleChipClick("Change the background color to ")}
            >
              🎨 Background
            </button>
            <button
              className="agent-chip"
              onClick={() => handleChipClick("Make the title text ")}
            >
              📝 Text Content
            </button>
            <button
              className="agent-chip"
              onClick={() => handleChipClick("Change layout to ")}
            >
              📐 Layout
            </button>
            <button
              className="agent-chip"
              onClick={() => handleChipClick("Increase font size of ")}
            >
              🔤 Font Size
            </button>
          </div>

          <form onSubmit={handleSendAgentMessage} className="agent-input-area">
            <input
              ref={inputRef}
              type="text"
              className="agent-input"
              placeholder={isListening ? '🎤 Listening... speak now' : (slide ? "Ask AI to edit this slide..." : "Please create or select a slide first")}
              value={agentInput}
              onChange={(e) => {
                setAgentInput(e.target.value);
                setBaseInput(e.target.value);
              }}
              disabled={isAgentLoading || !slide}
              style={{
                color: isListening ? '#6366F1' : undefined
              }}
            />
            {isSpeechSupported && (
              <button
                type="button"
                onClick={isListening ? stopListening : () => {
                  setBaseInput(agentInput);
                  startListening();
                }}
                title={isListening ? 'Stop listening' : 'Speak your edit'}
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: isListening ? '#EF4444' : '#6366F1',
                  color: '#fff',
                  fontSize: '16px',
                  animation: isListening ? 'pulse 1s infinite' : 'none',
                  transition: 'background 0.2s',
                  flexShrink: 0
                }}
              >
                {isListening ? '⏹' : '🎤'}
              </button>
            )}
            <button
              type="submit"
              className="agent-send-btn"
              disabled={!agentInput.trim() || isAgentLoading || !slide}
            >
              <Send size={16} />
            </button>
          </form>

          {isListening && (
            <div style={{
              textAlign: 'center',
              fontSize: '12px',
              color: '#EF4444',
              marginTop: '8px',
              paddingBottom: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}>
              <span style={{
                width: '8px', height: '8px',
                borderRadius: '50%',
                background: '#EF4444',
                animation: 'pulse 1s infinite'
              }} />
              Recording... click ⏹ to stop
            </div>
          )}

          {speechError && (
            <div style={{
              textAlign: 'center',
              fontSize: '12px',
              color: '#EF4444',
              marginTop: '8px',
              paddingBottom: '12px',
              paddingLeft: '14px',
              paddingRight: '14px',
              wordBreak: 'break-word'
            }}>
              ⚠️ {speechError}. Ensure mic access is allowed in your browser.
            </div>
          )}

          <style>{`
            @keyframes pulse {
              0%, 100% { opacity: 1; transform: scale(1); }
              50% { opacity: 0.7; transform: scale(1.1); }
            }
          `}</style>
        </div>
      )}
      {contextMenu && (
        <div
          style={{
            position: "fixed",
            left: contextMenu.x,
            top: contextMenu.y,
            background: "#ffffff",
            border: "1px solid #cfd6e3",
            borderRadius: "8px",
            boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
            zIndex: 9999,
            padding: "4px",
            display: "flex",
            flexDirection: "column",
            minWidth: "140px",
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => handleCutElement(contextMenu.elementId)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "8px 12px",
              background: "none",
              border: "none",
              width: "100%",
              textAlign: "left",
              cursor: "pointer",
              fontSize: "13px",
              fontWeight: 500,
              color: "#334155",
              borderRadius: "6px",
              transition: "background-color 0.15s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#f1f5f9")}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
          >
            <span>✂️</span>
            <span>Cut Element</span>
          </button>
          <button
            onClick={() => handleDeleteElement(contextMenu.elementId)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "8px 12px",
              background: "none",
              border: "none",
              width: "100%",
              textAlign: "left",
              cursor: "pointer",
              fontSize: "13px",
              fontWeight: 500,
              color: "#dc2626",
              borderRadius: "6px",
              transition: "background-color 0.15s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#fef2f2")}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
          >
            <span style={{ fontWeight: "bold" }}>❌</span>
            <span>Delete Element</span>
          </button>
        </div>
      )}
    </div>
  );
}

function IconButton({
  label,
  icon: Icon,
  onClick,
  disabled,
}: {
  label: string;
  icon: React.ComponentType<{ size?: number }>;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button className="icon-button" title={label} aria-label={label} onClick={onClick} disabled={disabled}>
      <Icon size={18} />
    </button>
  );
}

function SlideObject({
  element,
  selected,
  coordinateScaleX = 1,
  coordinateScaleY = 1,
  onContextMenu,
}: {
  element: SlideElement;
  selected: boolean;
  coordinateScaleX?: number;
  coordinateScaleY?: number;
  onContextMenu?: (x: number, y: number, elementId: string) => void;
}) {
  const { selectElement, updateElement } = useEditorStore();
  const objectRef = useRef<HTMLDivElement>(null);

  const startDrag = (event: React.PointerEvent<HTMLDivElement>) => {
    event.stopPropagation();
    selectElement(element.id);
    objectRef.current?.setPointerCapture(event.pointerId);
    const originX = event.clientX;
    const originY = event.clientY;
    const startX = element.x;
    const startY = element.y;
    const canvas = objectRef.current?.closest(".slide-frame, .slide-canvas") as HTMLElement | null;
    const bounds = canvas?.getBoundingClientRect();
    const designWidth = canvas?.classList.contains("slide-frame") ? FRAME_WIDTH : SLIDE_WIDTH;
    const designHeight = canvas?.classList.contains("slide-frame") ? FRAME_HEIGHT : SLIDE_HEIGHT;
    const actualScaleX = bounds ? bounds.width / designWidth : 1;
    const actualScaleY = bounds ? bounds.height / designHeight : 1;

    const onMove = (moveEvent: PointerEvent) => {
      updateElement(element.id, {
        x: Math.round(startX + (moveEvent.clientX - originX) / (actualScaleX * coordinateScaleX)),
        y: Math.round(startY + (moveEvent.clientY - originY) / (actualScaleY * coordinateScaleY)),
      });
    };
    const onUp = () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };

    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  };

  const startResizeCorner = (event: React.PointerEvent<HTMLDivElement>, corner: "tl" | "tr" | "bl" | "br") => {
    event.stopPropagation();
    event.preventDefault();
    const originX = event.clientX;
    const originY = event.clientY;
    const startX = element.x;
    const startY = element.y;
    const startWidth = element.width;
    const startHeight = element.height;
    
    const canvas = objectRef.current?.closest(".slide-frame, .slide-canvas") as HTMLElement | null;
    const bounds = canvas?.getBoundingClientRect();
    const designWidth = canvas?.classList.contains("slide-frame") ? FRAME_WIDTH : SLIDE_WIDTH;
    const designHeight = canvas?.classList.contains("slide-frame") ? FRAME_HEIGHT : SLIDE_HEIGHT;
    const actualScaleX = bounds ? bounds.width / designWidth : 1;
    const actualScaleY = bounds ? bounds.height / designHeight : 1;

    const onMove = (moveEvent: PointerEvent) => {
      const deltaX = (moveEvent.clientX - originX) / (actualScaleX * coordinateScaleX);
      const deltaY = (moveEvent.clientY - originY) / (actualScaleY * coordinateScaleY);
      
      const patch: Partial<SlideElement> = {};
      
      if (corner === "br") {
        patch.width = Math.max(10, Math.round(startWidth + deltaX));
        patch.height = Math.max(10, Math.round(startHeight + deltaY));
      } else if (corner === "bl") {
        const newWidth = Math.max(10, Math.round(startWidth - deltaX));
        patch.x = Math.round(startX + (startWidth - newWidth));
        patch.width = newWidth;
        patch.height = Math.max(10, Math.round(startHeight + deltaY));
      } else if (corner === "tr") {
        const newHeight = Math.max(10, Math.round(startHeight - deltaY));
        patch.y = Math.round(startY + (startHeight - newHeight));
        patch.width = Math.max(10, Math.round(startWidth + deltaX));
        patch.height = newHeight;
      } else if (corner === "tl") {
        const newWidth = Math.max(10, Math.round(startWidth - deltaX));
        const newHeight = Math.max(10, Math.round(startHeight - deltaY));
        patch.x = Math.round(startX + (startWidth - newWidth));
        patch.y = Math.round(startY + (startHeight - newHeight));
        patch.width = newWidth;
        patch.height = newHeight;
      }
      
      updateElement(element.id, patch);
    };
    
    const onUp = () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };

    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  };

  return (
    <div
      ref={objectRef}
      className={`slide-object ${selected ? "selected" : ""} kind-${element.kind}`}
      style={{
        left: element.x * coordinateScaleX,
        top: element.y * coordinateScaleY,
        width: element.width * coordinateScaleX,
        height: element.height * coordinateScaleY,
        color: element.color,
        background: element.kind === "text" ? "transparent" : element.fill,
        borderColor: element.stroke,
        borderRadius: element.radius ?? 6,
        fontSize: element.fontSize,
        fontWeight: element.fontWeight,
        textAlign: element.textAlign,
        transform: `rotate(${element.rotation ?? 0}deg)`,
      }}
      onPointerDown={startDrag}
      onContextMenu={(e) => {
        e.preventDefault();
        e.stopPropagation();
        onContextMenu?.(e.clientX, e.clientY, element.id);
      }}
    >
      <ElementRenderer element={element} isSelected={selected} onChange={(text) => updateElement(element.id, { text })} />
      {selected && (
        <>
          {/* Top-Left */}
          <div
            style={{
              position: "absolute",
              left: -4,
              top: -4,
              width: 8,
              height: 8,
              background: "#2563eb",
              border: "1px solid #ffffff",
              borderRadius: "50%",
              cursor: "nwse-resize",
              zIndex: 10,
            }}
            onPointerDown={(e) => startResizeCorner(e, "tl")}
          />
          {/* Top-Right */}
          <div
            style={{
              position: "absolute",
              right: -4,
              top: -4,
              width: 8,
              height: 8,
              background: "#2563eb",
              border: "1px solid #ffffff",
              borderRadius: "50%",
              cursor: "nesw-resize",
              zIndex: 10,
            }}
            onPointerDown={(e) => startResizeCorner(e, "tr")}
          />
          {/* Bottom-Left */}
          <div
            style={{
              position: "absolute",
              left: -4,
              bottom: -4,
              width: 8,
              height: 8,
              background: "#2563eb",
              border: "1px solid #ffffff",
              borderRadius: "50%",
              cursor: "nesw-resize",
              zIndex: 10,
            }}
            onPointerDown={(e) => startResizeCorner(e, "bl")}
          />
          {/* Bottom-Right */}
          <div
            style={{
              position: "absolute",
              right: -4,
              bottom: -4,
              width: 8,
              height: 8,
              background: "#2563eb",
              border: "1px solid #ffffff",
              borderRadius: "50%",
              cursor: "nwse-resize",
              zIndex: 10,
            }}
            onPointerDown={(e) => startResizeCorner(e, "br")}
          />
        </>
      )}
    </div>
  );
}

function ElementRenderer({
  element,
  onChange,
  isSelected,
}: {
  element: SlideElement;
  onChange?: (text: string) => void;
  isSelected?: boolean;
}) {
  const { selectElement } = useEditorStore();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isSelected && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isSelected]);

  if (element.kind === "image" && element.text && !element.text.includes("Image placeholder")) {
    return <img src={element.text} alt="Pasted slide visual" className="object-image" />;
  }

  if (element.kind === "icon") {
    return (
      <div className="icon-grid">
        {(element.items ?? []).map((item) => (
          <div className="icon-chip" key={item}>
            <Circle size={18} />
            <span>{item}</span>
          </div>
        ))}
      </div>
    );
  }

  if (element.kind === "flow") {
    return (
      <div className="flow-row">
        {(element.items ?? []).map((item, index) => (
          <div className="flow-step" key={item}>
            <span>{index + 1}</span>
            <p>{item}</p>
          </div>
        ))}
      </div>
    );
  }

  if (element.kind === "chart") {
    const items = element.items ?? [];
    return (
      <div className="chart-bars">
        {items.map((item, index) => (
          <div className="bar-wrap" key={item}>
            <div className="bar" style={{ height: `${42 + index * 16}%` }} />
            <span>{item}</span>
          </div>
        ))}
      </div>
    );
  }

  if (element.kind === "table") {
    return (
      <table className="mini-table">
        <tbody>
          {(element.items ?? []).map((item, index) => (
            <tr key={item}>
              <td>{index + 1}</td>
              <td>{item}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  if (element.kind === "text") {
    return (
      <textarea
        ref={textareaRef}
        className="object-text"
        value={element.text || ""}
        onChange={(e) => {
          onChange?.(e.target.value);
        }}
        onPointerDown={(e) => {
          e.stopPropagation();
          selectElement(element.id);
        }}
        onKeyDown={(e) => {
          e.stopPropagation();
        }}
        style={{
          width: "100%",
          height: "100%",
          border: "none",
          background: "transparent",
          resize: "none",
          outline: "none",
          fontFamily: "inherit",
          fontSize: "inherit",
          fontWeight: "inherit",
          color: "inherit",
          textAlign: "inherit",
          cursor: "text",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          overflow: "hidden",
          padding: 0,
          margin: 0,
        }}
      />
    );
  }

  return <div className="object-text">{element.text}</div>;
}

function Inspector({ element, slide, selectedZoneKey }: { element?: SlideElement; slide: Slide; selectedZoneKey?: string }) {
  const { updateElement, updateSlideLayout, updateSlideZone, updateSlideZoneStyle } = useEditorStore();

  if (selectedZoneKey) {
    const zoneValue = getZoneValue(slide, selectedZoneKey);
    const style = (slide.zone_content?.__styles?.[selectedZoneKey] || {}) as Partial<SlideElement>;
    const currentFontSize = style.fontSize ?? getDefaultZoneFontSize(selectedZoneKey);

    return (
      <div className="panel">
        <h2>Text</h2>
        <label>
          Content
          <textarea
            value={zoneValue}
            onChange={(event) => updateSlideZone(slide.id, selectedZoneKey, event.target.value)}
          />
        </label>
        <div className="field-grid">
          <label>
            Font size
            <input
              type="number"
              min="8"
              max="96"
              value={currentFontSize}
              onChange={(event) =>
                updateSlideZoneStyle(slide.id, selectedZoneKey, {
                  fontSize: Number(event.target.value),
                })
              }
            />
          </label>
          <label>
            Text color
            <input
              type="color"
              value={style.color ?? "#172033"}
              onChange={(event) => updateSlideZoneStyle(slide.id, selectedZoneKey, { color: event.target.value })}
            />
          </label>
        </div>
        <label>
          Alignment
          <div className="segmented-buttons">
            {[
              ["left", AlignLeft],
              ["center", AlignCenter],
              ["right", AlignRight],
              ["justify", AlignJustify],
            ].map(([value, Icon]) => (
              <button
                key={value as string}
                type="button"
                className={style.textAlign === value ? "active" : ""}
                title={`${value} align`}
                onClick={() => updateSlideZoneStyle(slide.id, selectedZoneKey, { textAlign: value as SlideElement["textAlign"] })}
              >
                <Icon size={16} />
              </button>
            ))}
          </div>
        </label>
      </div>
    );
  }

  if (!element) {
    return (
      <div className="panel slide-inspector">
        <h2>Slide Settings</h2>
        <div className="inspector-layout-info" style={{ marginTop: "10px" }}>
          <label style={{ fontSize: "11px", fontWeight: 700, textTransform: "uppercase", color: "#64748b" }}>Active Layout</label>
          <div style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "#ffffff",
            padding: "10px 12px",
            borderRadius: "6px",
            border: "1px solid #cad7e8",
            marginTop: "6px",
            marginBottom: "16px"
          }}>
            <span style={{ fontWeight: 700, fontSize: "14px" }}>
              {slide.layout_id || "None (Generic)"}
            </span>
            {slide.layout_score !== undefined && (
              <span style={{
                fontSize: "11px",
                fontWeight: 700,
                color: "#166534",
                background: "#f0fdf4",
                padding: "2px 6px",
                borderRadius: "10px"
              }}>
                Score: {Math.round(slide.layout_score * 100)}%
              </span>
            )}
          </div>
          
          <label htmlFor="inspector-layout-select" style={{ fontSize: "11px", fontWeight: 700, textTransform: "uppercase", color: "#64748b" }}>Manual Override</label>
          <select
            id="inspector-layout-select"
            value={slide.layout_id || ""}
            onChange={(e) => {
              const val = e.target.value;
              updateSlideLayout(slide.id, val ? (val as LayoutId) : undefined);
            }}
            style={{
              width: "100%",
              height: "32px",
              borderRadius: "6px",
              border: "1px solid #cad7e8",
              background: "#ffffff",
              padding: "0 8px",
              marginTop: "6px"
            }}
          >
            <option value="">None (Generic Canvas)</option>
            <option value="OneColumn">OneColumn</option>
            <option value="TwoColumn">TwoColumn</option>
            <option value="ThreeColumn">ThreeColumn</option>
            <option value="FourGrid">FourGrid</option>
            <option value="Hero">Hero</option>
            <option value="Dashboard">Dashboard</option>
            <option value="Architecture">Architecture</option>
            <option value="Timeline">Timeline</option>
            <option value="Comparison">Comparison</option>
            <option value="Process">Process</option>
          </select>
        </div>
        {slide.layout_id === "ThreeColumn" && (
          <div style={{ marginTop: "20px", borderTop: "1px solid #e2e8f0", paddingTop: "15px" }}>
            <span style={{ fontSize: "11px", fontWeight: 700, textTransform: "uppercase", color: "#64748b" }}>Grid Circle Images</span>
            {[1, 2, 3].map((num) => {
              const imgKey = `col_${num}_image`;
              const value = slide.zone_content?.[imgKey] || "";
              return (
                <div key={num} style={{ marginTop: "10px" }}>
                  <label htmlFor={`img-select-${num}`} style={{ fontSize: "11px", fontWeight: 600, color: "#475569" }}>
                    Column {num} Image
                  </label>
                  <div style={{ display: "flex", gap: "6px", marginTop: "4px" }}>
                    <input
                      id={`img-select-${num}`}
                      type="text"
                      placeholder="Image URL or Base64"
                      value={value}
                      onChange={(e) => updateSlideZone(slide.id, imgKey, e.target.value)}
                      style={{
                        flex: 1,
                        height: "28px",
                        borderRadius: "4px",
                        border: "1px solid #cad7e8",
                        padding: "0 6px",
                        fontSize: "11px"
                      }}
                    />
                    <input
                      type="file"
                      accept="image/*"
                      id={`file-input-${num}`}
                      style={{ display: "none" }}
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          const reader = new FileReader();
                          reader.onloadend = () => {
                            updateSlideZone(slide.id, imgKey, reader.result);
                          };
                          reader.readAsDataURL(file);
                        }
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => document.getElementById(`file-input-${num}`)?.click()}
                      style={{
                        height: "28px",
                        padding: "0 8px",
                        fontSize: "11px",
                        borderRadius: "4px",
                        border: "1px solid #cad7e8",
                        background: "#f8fafc",
                        cursor: "pointer",
                        fontWeight: 600
                      }}
                    >
                      Upload
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
        <div style={{ marginTop: "20px", fontSize: "12px", color: "#64748b", lineHeight: 1.5 }}>
          <p>Click text directly on the slide to edit it, or paste an image from the clipboard to add it to the current slide.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="panel">
      <h2>{element.kind}</h2>
      <label>
        Text
        <textarea
          value={element.text ?? (element.items ?? []).join("\n")}
          onChange={(event) => {
            const value = event.target.value;
            if (["icon", "flow", "chart", "table"].includes(element.kind)) {
              updateElement(element.id, { items: value.split("\n").filter(Boolean) });
            } else {
              updateElement(element.id, { text: value });
            }
          }}
        />
      </label>
      <div className="field-grid">
        <NumberField label="X" value={element.x} onChange={(x) => updateElement(element.id, { x })} />
        <NumberField label="Y" value={element.y} onChange={(y) => updateElement(element.id, { y })} />
        <NumberField label="W" value={element.width} onChange={(width) => updateElement(element.id, { width })} />
        <NumberField label="H" value={element.height} onChange={(height) => updateElement(element.id, { height })} />
      </div>
      <label>
        Font size
        <input
          type="number"
          min="8"
          max="96"
          value={element.fontSize ?? 20}
          onChange={(event) => updateElement(element.id, { fontSize: Number(event.target.value) })}
        />
      </label>
      <label>
        Alignment
        <div className="segmented-buttons">
          {[
            ["left", AlignLeft],
            ["center", AlignCenter],
            ["right", AlignRight],
            ["justify", AlignJustify],
          ].map(([value, Icon]) => (
            <button
              key={value as string}
              type="button"
              className={element.textAlign === value ? "active" : ""}
              title={`${value} align`}
              onClick={() => updateElement(element.id, { textAlign: value as SlideElement["textAlign"] })}
            >
              <Icon size={16} />
            </button>
          ))}
        </div>
      </label>
      <label>
        Font scale
        <input
          type="range"
          min="10"
          max="72"
          value={element.fontSize ?? 20}
          onChange={(event) => updateElement(element.id, { fontSize: Number(event.target.value) })}
        />
      </label>
      <label>
        Fill
        <input type="color" value={element.fill ?? "#ffffff"} onChange={(event) => updateElement(element.id, { fill: event.target.value })} />
      </label>
      <label>
        Text color
        <input type="color" value={element.color ?? "#172033"} onChange={(event) => updateElement(element.id, { color: event.target.value })} />
      </label>
    </div>
  );
}

function getZoneValue(slide: Slide, zoneKey: string) {
  const zone = slide.zone_content || {};
  const [root, child] = zoneKey.split(".");
  if (child !== undefined) {
    const source = Array.isArray(zone[root]) ? zone[root] : [];
    return String(source[Number(child)] || "");
  }
  return String(zone[zoneKey] ?? (zoneKey === "title" ? slide.title : ""));
}

function getDefaultZoneFontSize(zoneKey: string) {
  if (zoneKey === "title") return 42;
  if (zoneKey === "subtitle") return 22;
  if (zoneKey.includes("headline")) return 24;
  if (zoneKey.startsWith("cell_")) return 24;
  if (zoneKey.startsWith("col_")) return 17;
  if (zoneKey.startsWith("bullets.")) return 14;
  return 16;
}

function NumberField({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return (
    <label>
      {label}
      <input type="number" value={Math.round(value)} onChange={(event) => onChange(Number(event.target.value))} />
    </label>
  );
}
