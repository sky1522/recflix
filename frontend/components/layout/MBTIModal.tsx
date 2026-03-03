"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Check } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { getMBTIColor } from "@/lib/utils";
import type { MBTIType } from "@/types";

const MBTI_TYPES: MBTIType[] = [
  "INTJ", "INTP", "ENTJ", "ENTP",
  "INFJ", "INFP", "ENFJ", "ENFP",
  "ISTJ", "ISFJ", "ESTJ", "ESFJ",
  "ISTP", "ISFP", "ESTP", "ESFP",
];

const MBTI_GROUPS: Record<string, string> = {
  Analysts: "INTJ, INTP, ENTJ, ENTP",
  Diplomats: "INFJ, INFP, ENFJ, ENFP",
  Sentinels: "ISTJ, ISFJ, ESTJ, ESFJ",
  Explorers: "ISTP, ISFP, ESTP, ESFP",
};

function getMBTIGroupLabel(mbti: MBTIType): string {
  for (const [label, members] of Object.entries(MBTI_GROUPS)) {
    if (members.includes(mbti)) return label;
  }
  return "";
}

interface MBTIModalProps {
  onClose: () => void;
}

export default function MBTIModal({ onClose }: MBTIModalProps) {
  const { user, isAuthenticated, updateMBTI } = useAuthStore();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const [guestMBTI, setGuestMBTI] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      setGuestMBTI(localStorage.getItem("guest_mbti"));
    }
  }, [isAuthenticated]);

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
        'button:not([disabled]), [tabindex]:not([tabindex="-1"])'
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

  const currentMBTI = isAuthenticated ? user?.mbti : guestMBTI;

  const handleSelect = async (mbti: MBTIType) => {
    if (saving || mbti === currentMBTI) return;

    setSaving(true);
    setError(null);

    try {
      if (isAuthenticated) {
        await updateMBTI(mbti);
      } else {
        localStorage.setItem("guest_mbti", mbti);
        setGuestMBTI(mbti);
      }
      setSaved(true);
      setTimeout(() => onClose(), 1500);
    } catch {
      setError("저장에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setSaving(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose();
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
          aria-labelledby="mbti-modal-title"
          tabIndex={-1}
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="relative w-full max-w-md bg-surface-card rounded-xl overflow-hidden outline-none"
        >
          {/* Close Button */}
          <button
            onClick={onClose}
            aria-label="닫기"
            className="absolute top-3 right-3 z-10 w-8 h-8 bg-overlay/10 hover:bg-overlay/20 rounded-full flex items-center justify-center transition"
          >
            <X className="w-4 h-4 text-fg" />
          </button>

          {/* Content */}
          <div className="p-6">
            <h2 id="mbti-modal-title" className="text-xl font-bold text-fg mb-1">
              MBTI 설정
            </h2>
            <p className="text-sm text-fg/60 mb-5">
              MBTI를 설정하면 성격에 맞는 영화를 추천받을 수 있어요.
            </p>

            {/* Saved Feedback */}
            {saved && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 mb-4 px-3 py-2 bg-green-500/20 rounded-lg"
              >
                <Check className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">저장됨</span>
              </motion.div>
            )}

            {/* Error */}
            {error && (
              <div className="mb-4 px-3 py-2 bg-red-500/20 rounded-lg">
                <span className="text-sm text-red-400">{error}</span>
              </div>
            )}

            {/* 4x4 Grid */}
            <div className="grid grid-cols-4 gap-2">
              {MBTI_TYPES.map((mbti) => {
                const isActive = currentMBTI === mbti;
                const colorClass = getMBTIColor(mbti);
                return (
                  <button
                    key={mbti}
                    onClick={() => handleSelect(mbti)}
                    disabled={saving}
                    title={getMBTIGroupLabel(mbti)}
                    className={`relative px-2 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                      isActive
                        ? `${colorClass} text-white ring-2 ring-divider/50 scale-105`
                        : `bg-overlay/10 text-fg/80 hover:bg-overlay/20 hover:scale-105`
                    } ${saving ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
                  >
                    {mbti}
                    {isActive && (
                      <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full flex items-center justify-center">
                        <Check className="w-2.5 h-2.5 text-white" />
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Current MBTI info */}
            {currentMBTI && !saved && (
              <p className="mt-4 text-xs text-fg/40 text-center">
                현재: <span className="text-fg/60 font-medium">{currentMBTI}</span>
              </p>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
