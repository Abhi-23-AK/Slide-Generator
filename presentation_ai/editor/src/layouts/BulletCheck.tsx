import React from "react";
import { Check } from "lucide-react";

export const BulletCheck: React.FC = () => {
  return (
    <span 
      className="bullet-check flex-shrink-0"
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: "20px",
        height: "20px",
        borderRadius: "50%",
        backgroundColor: "#DCFCE7", // Light green background (bg-green-100)
        color: "#15803d", // Green check icon (text-green-700)
        marginTop: "3px",
      }}
    >
      <Check size={12} strokeWidth={4} />
    </span>
  );
};
