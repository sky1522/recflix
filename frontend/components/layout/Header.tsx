"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, Search, Heart, Star, Film, Home } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { WeatherIndicator } from "@/components/weather/WeatherBanner";
import SearchAutocomplete from "@/components/search/SearchAutocomplete";
import HeaderMobileDrawer from "@/components/layout/HeaderMobileDrawer";
import { WEATHER_CACHE_KEY } from "@/lib/constants";
import type { Weather } from "@/types";

const NAV_ITEMS = [
  { href: "/", label: "홈", icon: Home },
  { href: "/movies", label: "영화 검색", icon: Film },
] as const;

const AUTH_NAV_ITEMS = [
  { href: "/favorites", label: "찜 목록", icon: Heart },
  { href: "/ratings", label: "내 평점", icon: Star },
] as const;

export default function Header() {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [weather, setWeather] = useState<Weather | null>(null);

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

  // Load cached weather from localStorage (storage event only, no polling)
  const loadWeather = useCallback(() => {
    try {
      const cached = localStorage.getItem(WEATHER_CACHE_KEY);
      if (cached) {
        const { data } = JSON.parse(cached);
        setWeather(data);
      }
    } catch {
      // Ignore parse errors
    }
  }, []);

  useEffect(() => {
    loadWeather();
    window.addEventListener("storage", loadWeather);
    return () => window.removeEventListener("storage", loadWeather);
  }, [loadWeather]);

  const isActivePath = (path: string) => {
    if (path === "/") return pathname === "/";
    return pathname.startsWith(path);
  };

  return (
    <>
      <header
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrolled || mobileMenuOpen
            ? "bg-dark-200/95 backdrop-blur-sm shadow-lg"
            : "bg-gradient-to-b from-dark-300/80 to-transparent"
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
                      : "text-white/80 hover:text-white"
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
                        : "text-white/80 hover:text-white"
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
            </nav>

            {/* Right Section */}
            <div className="flex items-center space-x-2 md:space-x-4">
              {weather && (
                <div className="hidden lg:block">
                  <WeatherIndicator weather={weather} />
                </div>
              )}

              <button
                onClick={() => setSearchOpen(!searchOpen)}
                className="md:hidden p-2.5 text-white/70 hover:text-white transition min-w-[44px] min-h-[44px] flex items-center justify-center"
                aria-label="검색"
              >
                <Search className="w-5 h-5" />
              </button>

              <div className="hidden md:block w-64">
                <SearchAutocomplete
                  placeholder="영화 검색..."
                  compact
                  inputClassName="w-full bg-dark-100/50 border border-white/20 rounded-full pl-9 pr-8 py-1.5 text-sm text-white placeholder-white/50 focus:outline-none focus:border-primary-500 transition-all"
                />
              </div>

              {isAuthenticated ? (
                <div className="hidden md:flex items-center space-x-3">
                  <Link
                    href="/profile"
                    className="flex items-center space-x-2 text-white/80 hover:text-white transition"
                  >
                    <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center">
                      <span className="text-sm font-medium">
                        {user?.nickname?.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  </Link>
                  <button
                    onClick={logout}
                    className="text-sm text-white/60 hover:text-white transition"
                  >
                    로그아웃
                  </button>
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
                className="md:hidden p-2.5 text-white/70 hover:text-white transition z-10 min-w-[44px] min-h-[44px] flex items-center justify-center"
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
    </>
  );
}
