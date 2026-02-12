"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, Search, Heart, Star, Film, User, LogOut, Home } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { WeatherIndicator } from "@/components/weather/WeatherBanner";
import type { Weather } from "@/types";

export default function Header() {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [weather, setWeather] = useState<Weather | null>(null);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);

  // Load cached weather from localStorage
  useEffect(() => {
    const loadWeather = () => {
      try {
        const cached = localStorage.getItem("recflix_weather_v3");
        if (cached) {
          const { data } = JSON.parse(cached);
          setWeather(data);
        }
      } catch {
        // Ignore errors
      }
    };

    loadWeather();
    window.addEventListener("storage", loadWeather);
    const interval = setInterval(loadWeather, 5000);

    return () => {
      window.removeEventListener("storage", loadWeather);
      clearInterval(interval);
    };
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      window.location.href = `/movies?query=${encodeURIComponent(searchQuery)}`;
      setSearchOpen(false);
      setMobileMenuOpen(false);
    }
  };

  const navItems = [
    { href: "/", label: "홈", icon: Home },
    { href: "/movies", label: "영화 검색", icon: Film },
  ];

  const authNavItems = [
    { href: "/favorites", label: "찜 목록", icon: Heart },
    { href: "/ratings", label: "내 평점", icon: Star },
  ];

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
              {navItems.map((item) => (
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
                authNavItems.map((item) => (
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
              {/* Weather - Desktop only */}
              {weather && (
                <div className="hidden lg:block">
                  <WeatherIndicator weather={weather} />
                </div>
              )}

              {/* Search Button - Mobile */}
              <button
                onClick={() => setSearchOpen(!searchOpen)}
                className="md:hidden p-2 text-white/70 hover:text-white transition"
                aria-label="검색"
              >
                <Search className="w-5 h-5" />
              </button>

              {/* Search - Desktop */}
              <form onSubmit={handleSearch} className="hidden md:block relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="영화 검색..."
                  className="bg-dark-100/50 border border-white/20 rounded-full px-4 py-1.5 text-sm text-white placeholder-white/50 focus:outline-none focus:border-primary-500 transition-all w-48"
                />
              </form>

              {/* Auth - Desktop */}
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

              {/* Mobile Menu Toggle */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 text-white/70 hover:text-white transition z-10"
                aria-label="메뉴"
              >
                {mobileMenuOpen ? (
                  <X className="w-6 h-6" />
                ) : (
                  <Menu className="w-6 h-6" />
                )}
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
                className="md:hidden overflow-hidden"
              >
                <form onSubmit={handleSearch} className="pb-3">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="영화 제목, 배우, 감독 검색..."
                    className="w-full bg-dark-100 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-white/50 focus:outline-none focus:border-primary-500 transition"
                    autoFocus
                  />
                </form>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileMenuOpen(false)}
              className="fixed inset-0 bg-black/60 z-40 md:hidden"
            />

            {/* Menu Panel */}
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="fixed top-0 right-0 bottom-0 w-72 bg-dark-200 z-50 md:hidden shadow-2xl"
            >
              <div className="flex flex-col h-full pt-16">
                {/* Weather */}
                {weather && (
                  <div className="px-4 py-3 border-b border-white/10">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">
                        {weather.condition === "sunny" && "☀️"}
                        {weather.condition === "rainy" && "🌧️"}
                        {weather.condition === "cloudy" && "☁️"}
                        {weather.condition === "snowy" && "❄️"}
                      </span>
                      <div>
                        <p className="text-white font-medium">{weather.temperature}°C</p>
                        <p className="text-white/60 text-sm">{weather.city}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Navigation */}
                <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
                  {navItems.map((item) => {
                    const Icon = item.icon;
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition ${
                          isActivePath(item.href)
                            ? "bg-primary-600/20 text-primary-400"
                            : "text-white/80 hover:bg-white/5"
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                        <span>{item.label}</span>
                      </Link>
                    );
                  })}

                  {isAuthenticated && (
                    <>
                      <div className="h-px bg-white/10 my-2" />
                      {authNavItems.map((item) => {
                        const Icon = item.icon;
                        return (
                          <Link
                            key={item.href}
                            href={item.href}
                            className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition ${
                              isActivePath(item.href)
                                ? "bg-primary-600/20 text-primary-400"
                                : "text-white/80 hover:bg-white/5"
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
                <div className="px-4 py-4 border-t border-white/10">
                  {isAuthenticated ? (
                    <div className="space-y-3">
                      <Link
                        href="/profile"
                        className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-white/5 transition"
                      >
                        <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center">
                          <span className="font-medium">
                            {user?.nickname?.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <p className="text-white font-medium">{user?.nickname}</p>
                          <p className="text-white/60 text-sm">{user?.mbti || "MBTI 미설정"}</p>
                        </div>
                      </Link>
                      <button
                        onClick={() => {
                          logout();
                          setMobileMenuOpen(false);
                        }}
                        className="flex items-center space-x-3 px-4 py-3 w-full text-left text-white/60 hover:text-white hover:bg-white/5 rounded-lg transition"
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
                        className="block w-full px-4 py-3 bg-white/10 hover:bg-white/20 text-white text-center rounded-lg transition"
                      >
                        회원가입
                      </Link>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
