"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Home, Film, Heart, Star, LogOut, Settings, Sun, CloudRain, Cloud, CloudSnow, RotateCcw } from "lucide-react";
import { useWeather } from "@/hooks/useWeather";
import { useAuthStore } from "@/stores/authStore";
import { useMoodStore } from "@/stores/useMoodStore";
import { getMBTIColor } from "@/lib/utils";
import type { Weather, User as UserType, WeatherType, MoodType, MBTIType } from "@/types";

interface NavItem {
  href: string;
  label: string;
  icon: typeof Home;
}

interface HeaderMobileDrawerProps {
  weather: Weather | null;
  isAuthenticated: boolean;
  user: UserType | null;
  navItems: NavItem[];
  authNavItems: NavItem[];
  isActivePath: (path: string) => boolean;
  onClose: () => void;
  onLogout: () => void;
}

const WEATHER_OPTIONS: { type: WeatherType; icon: typeof Sun; label: string; color: string }[] = [
  { type: "sunny", icon: Sun, label: "맑음", color: "text-yellow-400" },
  { type: "rainy", icon: CloudRain, label: "비", color: "text-blue-400" },
  { type: "cloudy", icon: Cloud, label: "흐림", color: "text-gray-400" },
  { type: "snowy", icon: CloudSnow, label: "눈", color: "text-cyan-300" },
];

const MOOD_OPTIONS: { type: MoodType; emoji: string; label: string }[] = [
  { type: "relaxed", emoji: "😌", label: "평온한" },
  { type: "tense", emoji: "😰", label: "긴장된" },
  { type: "excited", emoji: "😆", label: "활기찬" },
  { type: "emotional", emoji: "💕", label: "몽글몽글한" },
  { type: "imaginative", emoji: "🔮", label: "상상에 빠진" },
  { type: "light", emoji: "😄", label: "유쾌한" },
  { type: "gloomy", emoji: "😢", label: "울적한" },
  { type: "stifled", emoji: "😤", label: "답답한" },
];

const WEATHER_EMOJIS: Record<WeatherType, string> = {
  sunny: "☀️",
  rainy: "🌧️",
  cloudy: "☁️",
  snowy: "❄️",
};

const MBTI_TYPES: MBTIType[] = [
  "INTJ", "INTP", "ENTJ", "ENTP",
  "INFJ", "INFP", "ENFJ", "ENFP",
  "ISTJ", "ISFJ", "ESTJ", "ESFJ",
  "ISTP", "ISFP", "ESTP", "ESFP",
];

export default function HeaderMobileDrawer({
  weather,
  isAuthenticated,
  user,
  navItems,
  authNavItems,
  isActivePath,
  onClose,
  onLogout,
}: HeaderMobileDrawerProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const { mood, setMood } = useMoodStore();
  const { isManual, setManualWeather, resetToRealWeather } = useWeather({ autoFetch: false });
  const { updateMBTI } = useAuthStore();

  // Guest MBTI state
  const [guestMBTI, setGuestMBTIState] = useState<string | null>(null);
  useEffect(() => {
    setGuestMBTIState(localStorage.getItem("guest_mbti"));
  }, []);
  const currentMBTI = isAuthenticated ? user?.mbti : guestMBTI;

  const handleMBTISelect = async (mbti: MBTIType) => {
    if (mbti === currentMBTI) return;
    if (isAuthenticated) {
      await updateMBTI(mbti);
    } else {
      localStorage.setItem("guest_mbti", mbti);
      setGuestMBTIState(mbti);
    }
  };

  useEffect(() => {
    const trigger = document.activeElement as HTMLElement | null;
    panelRef.current?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key !== "Tab" || !panelRef.current) return;

      const focusable = panelRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])'
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
      document.removeEventListener("keydown", handleKeyDown);
      trigger?.focus();
    };
  }, [onClose]);

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-black/60 z-40 md:hidden"
      />

      {/* Menu Panel */}
      <motion.div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label="메뉴"
        tabIndex={-1}
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 25, stiffness: 300 }}
        className="fixed top-0 right-0 bottom-0 w-72 bg-surface z-50 md:hidden shadow-2xl outline-none"
      >
        <div className="flex flex-col h-full pt-16 overflow-y-auto">
          {/* Weather Info + Selection */}
          {weather && (
            <div className="px-4 py-3 border-b border-divider/10">
              <div className="flex items-center space-x-3 mb-3">
                <span className="text-2xl">{WEATHER_EMOJIS[weather.condition]}</span>
                <div>
                  <p className="text-fg font-medium">{weather.temperature}°C</p>
                  <p className="text-fg/60 text-sm">{weather.city}</p>
                </div>
              </div>

              <p className="text-xs text-fg/50 mb-2">날씨 설정</p>
              <div className="grid grid-cols-4 gap-1.5">
                {WEATHER_OPTIONS.map((w) => {
                  const Icon = w.icon;
                  const isActive = weather.condition === w.type;
                  return (
                    <button
                      key={w.type}
                      onClick={() => setManualWeather(w.type)}
                      className={`flex flex-col items-center gap-1 py-2 rounded-lg transition-all min-h-[44px] ${
                        isActive
                          ? "bg-overlay/20 ring-1 ring-divider/30"
                          : "hover:bg-overlay/10 active:bg-overlay/15"
                      } ${w.color}`}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="text-[10px] text-fg/80">{w.label}</span>
                    </button>
                  );
                })}
              </div>
              {isManual && (
                <button
                  onClick={() => resetToRealWeather()}
                  className="flex items-center gap-1.5 w-full mt-2 px-2 py-1.5 rounded-lg text-xs text-fg/50 hover:text-fg hover:bg-overlay/10 transition"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>실시간 날씨로 돌아가기</span>
                </button>
              )}
            </div>
          )}

          {/* Mood Selection */}
          <div className="px-4 py-3 border-b border-divider/10">
            <p className="text-xs text-fg/50 mb-2">기분 설정</p>
            <div className="grid grid-cols-4 gap-1.5">
              {MOOD_OPTIONS.map((m) => {
                const isActive = mood === m.type;
                return (
                  <button
                    key={m.type}
                    onClick={() => setMood(mood === m.type ? null : m.type)}
                    className={`flex flex-col items-center gap-0.5 py-2 rounded-lg transition-all min-h-[44px] ${
                      isActive
                        ? "bg-overlay/20 ring-1 ring-divider/30 scale-105"
                        : "hover:bg-overlay/10 active:bg-overlay/15"
                    }`}
                  >
                    <span className="text-lg">{m.emoji}</span>
                    <span className="text-[10px] text-fg/80">{m.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* MBTI Selection */}
          <div className="px-4 py-3 border-b border-divider/10">
            <p className="text-xs text-fg/50 mb-2">MBTI 설정</p>
            <div className="grid grid-cols-4 gap-1.5">
              {MBTI_TYPES.map((mbti) => {
                const isActive = currentMBTI === mbti;
                return (
                  <button
                    key={mbti}
                    onClick={() => handleMBTISelect(mbti)}
                    className={`flex items-center justify-center py-2 rounded-lg transition-all min-h-[44px] text-xs font-semibold ${
                      isActive
                        ? `${getMBTIColor(mbti)} text-white ring-1 ring-divider/30`
                        : "bg-overlay/10 text-fg/80 hover:bg-overlay/15 active:bg-overlay/20"
                    }`}
                  >
                    {mbti}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-2 py-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition ${
                    isActivePath(item.href)
                      ? "bg-primary-600/20 text-primary-400"
                      : "text-fg/80 hover:bg-overlay/5"
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}

            {isAuthenticated && (
              <>
                <div className="h-px bg-overlay/10 my-2" />
                {authNavItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition ${
                        isActivePath(item.href)
                          ? "bg-primary-600/20 text-primary-400"
                          : "text-fg/80 hover:bg-overlay/5"
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </>
            )}
          </nav>

          {/* User Section */}
          <div className="px-4 py-4 border-t border-divider/10">
            {isAuthenticated ? (
              <div className="space-y-3">
                <Link
                  href="/profile"
                  className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-overlay/5 transition"
                >
                  <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center">
                    <span className="font-medium">
                      {user?.nickname?.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <p className="text-fg font-medium">{user?.nickname}</p>
                    <p className="text-fg/60 text-sm">{user?.mbti || "MBTI 미설정"}</p>
                  </div>
                </Link>
                <Link
                  href="/settings"
                  className="flex items-center space-x-3 px-4 py-3 rounded-lg text-fg/80 hover:bg-overlay/5 transition"
                >
                  <Settings className="w-5 h-5" />
                  <span>사용자 설정</span>
                </Link>
                <button
                  onClick={() => {
                    onLogout();
                    onClose();
                  }}
                  className="flex items-center space-x-3 px-4 py-3 w-full text-left text-fg/60 hover:text-fg hover:bg-overlay/5 rounded-lg transition"
                >
                  <LogOut className="w-5 h-5" />
                  <span>로그아웃</span>
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <Link
                  href="/login"
                  className="block w-full px-4 py-3 bg-primary-600 hover:bg-primary-700 text-white text-center font-medium rounded-lg transition"
                >
                  로그인
                </Link>
                <Link
                  href="/signup"
                  className="block w-full px-4 py-3 bg-overlay/10 hover:bg-overlay/20 text-fg text-center rounded-lg transition"
                >
                  회원가입
                </Link>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </>
  );
}
