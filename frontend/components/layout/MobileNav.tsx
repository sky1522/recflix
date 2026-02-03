"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Film, Heart, Star, User } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";

export default function MobileNav() {
  const pathname = usePathname();
  const { isAuthenticated } = useAuthStore();

  const isActive = (path: string) => {
    if (path === "/") return pathname === "/";
    return pathname.startsWith(path);
  };

  const navItems = [
    { href: "/", icon: Home, label: "홈" },
    { href: "/movies", icon: Film, label: "영화" },
    { href: "/favorites", icon: Heart, label: "찜", requireAuth: true },
    { href: "/ratings", icon: Star, label: "평점", requireAuth: true },
    { href: isAuthenticated ? "/profile" : "/login", icon: User, label: isAuthenticated ? "프로필" : "로그인" },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-dark-200/95 backdrop-blur-sm border-t border-white/10 md:hidden safe-area-bottom">
      <div className="flex items-center justify-around h-16">
        {navItems.map((item) => {
          // Skip auth-required items for non-authenticated users
          if (item.requireAuth && !isAuthenticated) {
            return null;
          }

          const Icon = item.icon;
          const active = isActive(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
                active ? "text-primary-500" : "text-white/60"
              }`}
            >
              <Icon className={`w-5 h-5 ${active ? "fill-current" : ""}`} />
              <span className="text-xs mt-1">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
