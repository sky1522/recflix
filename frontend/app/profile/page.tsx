"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Settings, ChevronRight } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { getMBTIColor } from "@/lib/utils";
import type { MBTIType } from "@/types";

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated, fetchUser } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    fetchUser();
  }, [isAuthenticated, router, fetchUser]);

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-12 px-4 bg-surface">
      <div className="max-w-2xl mx-auto">
        {/* Profile Header */}
        <div className="bg-surface-card rounded-lg p-8 mb-6 border border-divider/10">
          <div className="flex items-center space-x-4">
            <div className="w-20 h-20 rounded-full bg-primary-600 flex items-center justify-center">
              <span className="text-3xl font-bold text-white">
                {user.nickname.charAt(0).toUpperCase()}
              </span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-fg">{user.nickname}</h1>
              <p className="text-fg/60">{user.email}</p>
              {user.mbti && (
                <span className={`inline-block mt-2 px-3 py-1 rounded-full text-sm text-white ${getMBTIColor(user.mbti as MBTIType)}`}>
                  {user.mbti}
                </span>
              )}
              {user.auth_provider && (
                <p className="text-fg/40 text-xs mt-1">
                  {user.auth_provider === "kakao" ? "카카오" : user.auth_provider === "google" ? "Google" : "이메일"} 로그인
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Settings Link */}
        <Link
          href="/settings"
          className="flex items-center justify-between bg-surface-card rounded-lg p-5 border border-divider/10 hover:bg-overlay/5 transition"
        >
          <div className="flex items-center gap-3">
            <Settings className="w-5 h-5 text-fg/60" />
            <div>
              <p className="text-fg font-medium">사용자 설정</p>
              <p className="text-fg/50 text-sm">MBTI, 선호 장르, 테마 등을 설정하세요</p>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-fg/30" />
        </Link>
      </div>
    </div>
  );
}
