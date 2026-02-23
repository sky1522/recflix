"use client";

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";

interface TrailerModalProps {
  trailerKey: string;
  onClose: () => void;
}

export default function TrailerModal({ trailerKey, onClose }: TrailerModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.body.style.overflow = "hidden";
    const trigger = document.activeElement as HTMLElement | null;
    dialogRef.current?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key !== "Tab" || !dialogRef.current) return;

      const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
        "button:not([disabled]), [tabindex]:not([tabindex=\"-1\"])"
      );
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = "unset";
      document.removeEventListener("keydown", handleKeyDown);
      trigger?.focus();
    };
  }, [onClose]);

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80"
        onClick={handleBackdropClick}
      >
        <motion.div
          ref={dialogRef}
          role="dialog"
          aria-modal="true"
          aria-label="트레일러"
          tabIndex={-1}
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="relative w-full max-w-4xl"
        >
          <button
            onClick={onClose}
            aria-label="닫기"
            className="absolute -top-12 right-0 w-10 h-10 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center transition"
          >
            <X className="w-6 h-6 text-white" />
          </button>

          <div className="aspect-video rounded-xl overflow-hidden bg-dark-100">
            <iframe
              src={`https://www.youtube.com/embed/${trailerKey}?autoplay=1`}
              title="트레일러"
              className="w-full h-full"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
