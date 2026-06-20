import React from "react";

interface EditingOverlayProps {
  /** Whether the editor is in "edit canvas" mode */
  active: boolean;
  children?: React.ReactNode;
}

/**
 * Transparent overlay rendered on top of the slide content when the
 * user is in edit mode. Provides selection outlines, drag handles, etc.
 * When not active this renders nothing.
 */
export const EditingOverlay: React.FC<EditingOverlayProps> = ({ active, children }) => {
  if (!active) return null;

  return (
    <div
      className="slide-editing-overlay"
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 10,
        pointerEvents: "none",
      }}
    >
      {children}
    </div>
  );
};
