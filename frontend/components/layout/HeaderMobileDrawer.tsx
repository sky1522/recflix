"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Home, Film, Heart, Star, User, LogOut } from "lucide-react";
import type { Weather, User as UserType } from "@/types";

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
                    onLogout();
                    onClose();
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
  );
}
