"use client";

interface HighlightTextProps {
  text: string;
  query: string;
  className?: string;
  highlightClassName?: string;
}

export default function HighlightText({
  text,
  query,
  className = "",
  highlightClassName = "font-bold text-primary-400",
}: HighlightTextProps) {
  if (!query.trim()) {
    return <span className={className}>{text}</span>;
  }

  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const parts = text.split(new RegExp(`(${escaped})`, "gi"));

  return (
    <span className={className}>
      {parts.map((part, i) =>
        part.toLowerCase() === query.toLowerCase() ? (
          <span key={i} className={highlightClassName}>
            {part}
          </span>
        ) : (
          part
        )
      )}
    </span>
  );
}
