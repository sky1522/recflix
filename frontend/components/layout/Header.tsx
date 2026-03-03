"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, Search, Heart, Star, Film, Home, Sun, CloudRain, Cloud, CloudSnow, RotateCcw, Settings, LogOut } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { useMoodStore } from "@/stores/useMoodStore";
import { useWeather } from "@/hooks/useWeather";
import SearchAutocomplete from "@/components/search/SearchAutocomplete";
import HeaderMobileDrawer from "@/components/layout/HeaderMobileDrawer";
import MBTIModal from "@/components/layout/MBTIModal";
import type { WeatherType, MoodType } from "@/types";

const NAV_ITEMS = [
  { href: "/", label: "홈", icon: Home },
  { href: "/movies", label: "영화 검색", icon: Film },
] as const;

const AUTH_NAV_ITEMS = [
  { href: "/favorites", label: "찜 목록", icon: Heart },
  { href: "/ratings", label: "내 평점", icon: Star },
] as const;

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

type DropdownType = "weather" | "mood" | "profile" | null;

function useGuestMBTI() {
  const [guestMBTI, setGuestMBTI] = useState<string | null>(null);
  useEffect(() => {
    setGuestMBTI(localStorage.getItem("guest_mbti"));
  }, []);
  const update = (mbti: string) => {
    localStorage.setItem("guest_mbti", mbti);
    setGuestMBTI(mbti);
  };
  return { guestMBTI, setGuestMBTI: update };
}

function MBTIBadge({ user, isAuthenticated, onClick }: { user: { mbti?: string | null } | null; isAuthenticated: boolean; onClick: () => void }) {
  const { guestMBTI } = useGuestMBTI();
  const mbti = isAuthenticated ? user?.mbti : guestMBTI;
  return (
    <button
      onClick={onClick}
      className="hidden md:flex items-center px-2.5 py-1 rounded-full bg-overlay/10 hover:bg-overlay/15 transition text-xs text-fg/80 hover:text-fg"
      title={mbti ? `MBTI: ${mbti}` : "MBTI 설정하기"}
    >
      {mbti ? (
        <span className="font-semibold text-primary-400">{mbti}</span>
      ) : (
        <span className="text-fg/50">MBTI 설정</span>
      )}
    </button>
  );
}

export default function Header() {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuthStore();
  const { mood, setMood } = useMoodStore();
  const { weather, isManual, setManualWeather, resetToRealWeather } = useWeather({ autoFetch: true });

  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [openDropdown, setOpenDropdown] = useState<DropdownType>(null);
  const [mbtiModalOpen, setMbtiModalOpen] = useState(false);

  const weatherDropdownRef = useRef<HTMLDivElement>(null);
  const moodDropdownRef = useRef<HTMLDivElement>(null);
  const profileDropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close mobile menu on route change
  useEffect(() => { setMobileMenuOpen(false); }, [pathname]);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    document.body.style.overflow = mobileMenuOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [mobileMenuOpen]);

  // Close dropdown on outside click or ESC
  useEffect(() => {
    if (!openDropdown) return;

    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      const refs = [weatherDropdownRef, moodDropdownRef, profileDropdownRef];
      const clickedInsideAny = refs.some((ref) => ref.current?.contains(target));
      if (!clickedInsideAny) {
        setOpenDropdown(null);
      }
    };
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpenDropdown(null);
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEsc);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEsc);
    };
  }, [openDropdown]);

  const isActivePath = (path: string) => {
    if (path === "/") return pathname === "/";
    return pathname.startsWith(path);
  };

  const toggleDropdown = (type: DropdownType) => {
    setOpenDropdown((prev) => (prev === type ? null : type));
  };

  const handleWeatherSelect = (condition: WeatherType) => {
    setManualWeather(condition);
    setOpenDropdown(null);
  };

  const handleResetWeather = async () => {
    await resetToRealWeather();
    setOpenDropdown(null);
  };

  const handleMoodSelect = (m: MoodType) => {
    setMood(mood === m ? null : m);
    if (mood !== m) setOpenDropdown(null);
  };

  const currentMoodOption = mood ? MOOD_OPTIONS.find((o) => o.type === mood) : null;

  const dropdownAnimation = {
    initial: { opacity: 0, scale: 0.95, y: -4 },
    animate: { opacity: 1, scale: 1, y: 0 },
    exit: { opacity: 0, scale: 0.95, y: -4 },
    transition: { duration: 0.15 },
  };

  return (
    <>
      <header
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrolled || mobileMenuOpen
            ? "bg-surface/95 backdrop-blur-sm shadow-lg"
            : "bg-gradient-to-b from-surface-deep/80 to-transparent"
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="flex items-center justify-between h-14 md:h-16">
            {/* Logo */}
            <Link
              href="/"
              onClick={(e) => {
                if (pathname === "/") {
                  e.preventDefault();
                  window.location.reload();
                }
              }}
              className="flex items-center gap-0.5 z-10"
            >
              <svg viewBox="0 0 32 32" className="w-7 h-7 md:w-8 md:h-8">
                <rect width="32" height="32" rx="6" fill="#e50914"/>
                <path d="M10 7h8a5 5 0 0 1 0 10h-1l5 8h-4l-5-8h-0V25h-3V7zm3 3v5h5a2.5 2.5 0 0 0 0-5z" fill="white"/>
              </svg>
              <span className="text-xl md:text-2xl font-bold text-primary-500">ecflix</span>
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-6">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`transition ${
                    isActivePath(item.href)
                      ? "text-primary-400 font-medium"
                      : "text-fg/80 hover:text-fg"
                  }`}
                >
                  {item.label}
                </Link>
              ))}
              {isAuthenticated &&
                AUTH_NAV_ITEMS.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`transition ${
                      isActivePath(item.href)
                        ? "text-primary-400 font-medium"
                        : "text-fg/80 hover:text-fg"
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
            </nav>

            {/* Right Section */}
            <div className="flex items-center space-x-1 md:space-x-3">
              {/* Weather Dropdown (desktop) */}
              {weather && (
                <div ref={weatherDropdownRef} className="relative hidden md:block">
                  <button
                    onClick={() => toggleDropdown("weather")}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full transition-all text-sm ${
                      openDropdown === "weather"
                        ? "bg-overlay/20 ring-1 ring-divider/30"
                        : "bg-overlay/10 hover:bg-overlay/15"
                    }`}
                    aria-expanded={openDropdown === "weather"}
                    aria-haspopup="true"
                  >
                    <span className="text-base">{WEATHER_EMOJIS[weather.condition]}</span>
                    <span className="font-medium text-fg">{weather.temperature}°C</span>
                  </button>

                  <AnimatePresence>
                    {openDropdown === "weather" && (
                      <motion.div
                        {...dropdownAnimation}
                        className="absolute right-0 top-full mt-2 w-56 bg-surface-card/95 backdrop-blur-md rounded-xl border border-divider/15 shadow-2xl p-3 z-50"
                        role="menu"
                      >
                        <p className="text-xs text-fg/50 mb-2 px-1">날씨에 따른 영화추천</p>
                        <div className="grid grid-cols-2 gap-1.5">
                          {WEATHER_OPTIONS.map((w) => {
                            const Icon = w.icon;
                            const isActive = weather.condition === w.type;
                            return (
                              <button
                                key={w.type}
                                onClick={() => handleWeatherSelect(w.type)}
                                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all ${
                                  isActive
                                    ? "bg-overlay/20 ring-1 ring-divider/30"
                                    : "hover:bg-overlay/10"
                                } ${w.color}`}
                                role="menuitem"
                              >
                                <Icon className="w-4 h-4" />
                                <span className="text-fg/90">{w.label}</span>
                              </button>
                            );
                          })}
                        </div>
                        {isManual && (
                          <button
                            onClick={handleResetWeather}
                            className="flex items-center gap-2 w-full mt-2 px-3 py-2 rounded-lg text-xs text-fg/60 hover:text-fg hover:bg-overlay/10 transition"
                          >
                            <RotateCcw className="w-3.5 h-3.5" />
                            <span>실시간 날씨로 돌아가기</span>
                          </button>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}

              {/* Mood Dropdown (desktop) */}
              <div ref={moodDropdownRef} className="relative hidden md:block">
                <button
                  onClick={() => toggleDropdown("mood")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full transition-all text-sm ${
                    openDropdown === "mood"
                      ? "bg-overlay/20 ring-1 ring-divider/30"
                      : "bg-overlay/10 hover:bg-overlay/15"
                  }`}
                  aria-expanded={openDropdown === "mood"}
                  aria-haspopup="true"
                >
                  <span className="text-base">{currentMoodOption?.emoji ?? "😊"}</span>
                  <span className="text-fg/80 text-xs">
                    {currentMoodOption?.label ?? "기분"}
                  </span>
                </button>

                <AnimatePresence>
                  {openDropdown === "mood" && (
                    <motion.div
                      {...dropdownAnimation}
                      className="absolute right-0 top-full mt-2 w-64 bg-surface-card/95 backdrop-blur-md rounded-xl border border-divider/15 shadow-2xl p-3 z-50"
                      role="menu"
                    >
                      <p className="text-xs text-fg/50 mb-2 px-1">지금 기분이 어떠세요?</p>
                      <div className="grid grid-cols-2 gap-1.5">
                        {MOOD_OPTIONS.map((m) => {
                          const isActive = mood === m.type;
                          return (
                            <button
                              key={m.type}
                              onClick={() => handleMoodSelect(m.type)}
                              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all ${
                                isActive
                                  ? "bg-overlay/20 ring-1 ring-divider/30"
                                  : "hover:bg-overlay/10"
                              }`}
                              role="menuitem"
                            >
                              <span className="text-base">{m.emoji}</span>
                              <span className="text-fg/90">{m.label}</span>
                            </button>
                          );
                        })}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* MBTI Badge (desktop) — visible for all users */}
              <MBTIBadge
                user={user}
                isAuthenticated={isAuthenticated}
                onClick={() => setMbtiModalOpen(true)}
              />

              <button
                onClick={() => setSearchOpen(!searchOpen)}
                className="md:hidden p-2.5 text-fg/70 hover:text-fg transition min-w-[44px] min-h-[44px] flex items-center justify-center"
                aria-label="검색"
              >
                <Search className="w-5 h-5" />
              </button>

              <div className="hidden md:block w-64">
                <SearchAutocomplete
                  placeholder="영화 검색..."
                  compact
                  inputClassName="w-full bg-surface-card/50 border border-divider/20 rounded-full pl-9 pr-8 py-1.5 text-sm text-fg placeholder-fg/50 focus:outline-none focus:border-primary-500 transition-all"
                />
              </div>

              {isAuthenticated ? (
                <div ref={profileDropdownRef} className="relative hidden md:block">
                  <button
                    onClick={() => toggleDropdown("profile")}
                    className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center hover:ring-2 hover:ring-primary-400/50 transition"
                    aria-expanded={openDropdown === "profile"}
                    aria-haspopup="true"
                  >
                    <span className="text-sm font-medium text-white">
                      {user?.nickname?.charAt(0).toUpperCase()}
                    </span>
                  </button>

                  <AnimatePresence>
                    {openDropdown === "profile" && (
                      <motion.div
                        {...dropdownAnimation}
                        className="absolute right-0 top-full mt-2 w-56 bg-surface-card/95 backdrop-blur-md rounded-xl border border-divider/15 shadow-2xl z-50 overflow-hidden"
                        role="menu"
                      >
                        {/* User Info */}
                        <div className="px-4 py-3 border-b border-divider/10">
                          <p className="text-sm font-medium text-fg">{user?.nickname}</p>
                          <p className="text-xs text-fg/50">{user?.email}</p>
                        </div>

                        {/* Menu Items */}
                        <div className="py-1">
                          <Link
                            href="/settings"
                            onClick={() => setOpenDropdown(null)}
                            className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-fg/80 hover:bg-overlay/10 transition"
                            role="menuitem"
                          >
                            <Settings className="w-4 h-4" />
                            <span>사용자 설정</span>
                          </Link>
                          <Link
                            href="/favorites"
                            onClick={() => setOpenDropdown(null)}
                            className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-fg/80 hover:bg-overlay/10 transition"
                            role="menuitem"
                          >
                            <Heart className="w-4 h-4" />
                            <span>찜 목록</span>
                          </Link>
                          <Link
                            href="/ratings"
                            onClick={() => setOpenDropdown(null)}
                            className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-fg/80 hover:bg-overlay/10 transition"
                            role="menuitem"
                          >
                            <Star className="w-4 h-4" />
                            <span>내 평점</span>
                          </Link>
                        </div>

                        {/* Logout */}
                        <div className="border-t border-divider/10 py-1">
                          <button
                            onClick={() => {
                              logout();
                              setOpenDropdown(null);
                            }}
                            className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-fg/60 hover:text-red-400 hover:bg-overlay/10 transition"
                            role="menuitem"
                          >
                            <LogOut className="w-4 h-4" />
                            <span>로그아웃</span>
                          </button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ) : (
                <Link
                  href="/login"
                  className="hidden md:block bg-primary-600 hover:bg-primary-700 text-white px-4 py-1.5 rounded-md text-sm font-medium transition"
                >
                  로그인
                </Link>
              )}

              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2.5 text-fg/70 hover:text-fg transition z-10 min-w-[44px] min-h-[44px] flex items-center justify-center"
                aria-label="메뉴"
              >
                {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>

          {/* Mobile Search Bar */}
          <AnimatePresence>
            {searchOpen && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="md:hidden overflow-visible pb-3"
              >
                <SearchAutocomplete
                  placeholder="영화 제목, 배우, 감독 검색..."
                  onClose={() => setSearchOpen(false)}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </header>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <HeaderMobileDrawer
            weather={weather}
            isAuthenticated={isAuthenticated}
            user={user}
            navItems={[...NAV_ITEMS]}
            authNavItems={[...AUTH_NAV_ITEMS]}
            isActivePath={isActivePath}
            onClose={() => setMobileMenuOpen(false)}
            onLogout={logout}
          />
        )}
      </AnimatePresence>

      {/* MBTI Modal */}
      {mbtiModalOpen && <MBTIModal onClose={() => setMbtiModalOpen(false)} />}
    </>
  );
}
