"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { CERTIFICATION_TOOLTIPS, DEFAULT_TOOLTIP } from "@/lib/certificationTooltips";

const CERT_BADGE_COLORS: Record<string, string> = {
  ALL: "bg-green-600",
  G: "bg-green-600",
  PG: "bg-blue-600",
  "12": "bg-blue-600",
  "PG-13": "bg-yellow-600",
  "15": "bg-yellow-600",
  R: "bg-red-600",
  "18": "bg-red-600",
  "19": "bg-red-600",
  "NC-17": "bg-red-600",
  NR: "bg-red-600",
  UR: "bg-red-600",
};

const CERT_BORDER_COLORS: Record<string, string> = {
  ALL: "border-green-500/50 text-green-400",
  G: "border-green-500/50 text-green-400",
  PG: "border-blue-500/50 text-blue-400",
  "12": "border-blue-500/50 text-blue-400",
  "PG-13": "border-yellow-500/50 text-yellow-400",
  "15": "border-yellow-500/50 text-yellow-400",
  R: "border-red-500/50 text-red-400",
  "18": "border-red-500/50 text-red-400",
  "19": "border-red-500/50 text-red-400",
  "NC-17": "border-red-500/50 text-red-400",
  NR: "border-red-500/50 text-red-400",
  UR: "border-red-500/50 text-red-400",
};

type BadgeVariant = "filled" | "outlined" | "outlined-white";

interface CertificationBadgeProps {
  certification: string | null | undefined;
  variant?: BadgeVariant;
  className?: string;
}

export default function CertificationBadge({ certification, variant = "filled", className = "" }: CertificationBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const badgeRef = useRef<HTMLSpanElement>(null);

  const handleTouchToggle = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setShowTooltip((prev) => !prev);
  }, []);

  const tooltipInfo = certification
    ? CERTIFICATION_TOOLTIPS[certification] ?? DEFAULT_TOOLTIP
    : null;

  if (!certification || !tooltipInfo) return null;

  const badgeStyle =
    variant === "filled"
      ? `${CERT_BADGE_COLORS[certification] ?? "bg-gray-600"} text-white text-[10px] font-bold px-1.5 py-0.5 rounded`
      : variant === "outlined"
        ? `border ${CERT_BORDER_COLORS[certification] ?? "border-white/30 text-white/60"} px-1.5 py-0.5 rounded text-xs font-medium`
        : `border border-white/30 text-white px-1.5 md:px-2 py-0.5 rounded text-xs`;

  return (
    <span
      ref={badgeRef}
      className={`inline-flex items-center cursor-help ${className}`}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      onTouchEnd={handleTouchToggle}
      aria-label={`${certification} — ${tooltipInfo.label}: ${tooltipInfo.description}`}
    >
      <span className={badgeStyle}>{certification}</span>

      {showTooltip && (
        <PortalTooltip
          label={tooltipInfo.label}
          description={tooltipInfo.description}
          badgeRef={badgeRef}
          onClose={() => setShowTooltip(false)}
        />
      )}
    </span>
  );
}

function PortalTooltip({
  label,
  description,
  badgeRef,
  onClose,
}: {
  label: string;
  description: string;
  badgeRef: React.RefObject<HTMLSpanElement | null>;
  onClose: () => void;
}) {
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [coords, setCoords] = useState<{ top: number; left: number; arrowUp: boolean } | null>(null);

  useEffect(() => {
    if (!badgeRef.current || !tooltipRef.current) return;
    const badge = badgeRef.current.getBoundingClientRect();
    const tooltip = tooltipRef.current.getBoundingClientRect();

    const centerX = badge.left + badge.width / 2;
    let left = centerX - tooltip.width / 2;
    // Clamp to viewport
    left = Math.max(8, Math.min(left, window.innerWidth - tooltip.width - 8));

    const spaceBelow = window.innerHeight - badge.bottom;
    const arrowUp = spaceBelow >= tooltip.height + 8;
    const top = arrowUp
      ? badge.bottom + 8
      : badge.top - tooltip.height - 8;

    setCoords({ top, left, arrowUp });
  }, [badgeRef]);

  // Close on outside touch (mobile)
  useEffect(() => {
    const handleTouch = (e: TouchEvent) => {
      if (badgeRef.current && !badgeRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener("touchstart", handleTouch);
    return () => document.removeEventListener("touchstart", handleTouch);
  }, [badgeRef, onClose]);

  const arrowStyle = coords?.arrowUp
    ? "top-0 -translate-y-full border-l-transparent border-r-transparent border-t-transparent border-b-[rgba(0,0,0,0.85)] border-b-[6px] border-l-[6px] border-r-[6px] border-t-0"
    : "bottom-0 translate-y-full border-l-transparent border-r-transparent border-b-transparent border-t-[rgba(0,0,0,0.85)] border-t-[6px] border-l-[6px] border-r-[6px] border-b-0";

  return createPortal(
    <div
      ref={tooltipRef}
      style={coords ? { top: coords.top, left: coords.left } : { top: -9999, left: -9999 }}
      className="fixed z-[9999] max-w-[200px] px-3 py-2 rounded-lg shadow-lg bg-[rgba(0,0,0,0.85)] text-white animate-tooltip-fade pointer-events-none"
    >
      {coords && (
        <span
          className={`absolute ${arrowStyle} w-0 h-0`}
          style={{ left: badgeRef.current ? badgeRef.current.getBoundingClientRect().left + badgeRef.current.getBoundingClientRect().width / 2 - (coords?.left ?? 0) : "50%" }}
        />
      )}
      <p className="text-[13px] font-semibold leading-tight">{label}</p>
      <p className="text-[12px] text-white/80 leading-snug mt-0.5">{description}</p>
    </div>,
    document.body
  );
}
