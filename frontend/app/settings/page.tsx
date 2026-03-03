"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  User as UserIcon,
  Heart,
  Star,
  Sun,
  Moon,
  Check,
  ChevronRight,
  LogOut,
  Trash2,
  Pencil,
} from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { useThemeStore } from "@/stores/themeStore";
import MBTIModal from "@/components/layout/MBTIModal";
import { getMBTIColor } from "@/lib/utils";
import * as api from "@/lib/api";
import Link from "next/link";
import type { MBTIType } from "@/types";

const GENRE_OPTIONS = [
  "액션", "로맨스", "코미디", "공포", "스릴러",
  "SF", "드라마", "애니메이션", "범죄", "판타지",
] as const;

export default function SettingsPage() {
  const router = useRouter();
  const { user, isAuthenticated, logout, fetchUser } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();

  const [mbtiModalOpen, setMbtiModalOpen] = useState(false);
  const [editingNickname, setEditingNickname] = useState(false);
  const [nickname, setNickname] = useState("");
  const [savingNickname, setSavingNickname] = useState(false);

  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [savingGenres, setSavingGenres] = useState(false);
  const [genresSaved, setGenresSaved] = useState(false);

  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (user) {
      setNickname(user.nickname || "");
      setSelectedGenres(user.preferred_genres || []);
    }
  }, [user]);

  const handleSaveNickname = useCallback(async () => {
    if (!nickname.trim() || nickname === user?.nickname) {
      setEditingNickname(false);
      return;
    }
    setSavingNickname(true);
    try {
      await api.updateUser({ nickname: nickname.trim() });
      await fetchUser();
      setEditingNickname(false);
    } catch {
      // revert
      setNickname(user?.nickname || "");
    } finally {
      setSavingNickname(false);
    }
  }, [nickname, user?.nickname, fetchUser]);

  const toggleGenre = (genre: string) => {
    setSelectedGenres((prev) =>
      prev.includes(genre) ? prev.filter((g) => g !== genre) : [...prev, genre]
    );
    setGenresSaved(false);
  };

  const handleSaveGenres = async () => {
    if (selectedGenres.length < 3) return;
    setSavingGenres(true);
    try {
      await api.completeOnboarding(selectedGenres);
      await fetchUser();
      setGenresSaved(true);
      setTimeout(() => setGenresSaved(false), 2000);
    } catch {
      // silently fail
    } finally {
      setSavingGenres(false);
    }
  };

  const handleDeleteAccount = async () => {
    setDeleting(true);
    try {
      await api.deleteAccount();
      logout();
      router.replace("/");
    } catch {
      setDeleting(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.replace("/");
  };

  if (!isAuthenticated || !user) return null;

  const genresChanged =
    JSON.stringify([...selectedGenres].sort()) !==
    JSON.stringify([...(user.preferred_genres || [])].sort());

  return (
    <div className="min-h-screen bg-surface">
      <div className="max-w-2xl mx-auto px-4 py-8 md:py-12">
        <h1 className="text-2xl font-bold text-fg mb-8">설정</h1>

        {/* Profile Section */}
        <Section title="프로필">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-14 h-14 rounded-full bg-primary-600 flex items-center justify-center shrink-0">
              <span className="text-xl font-bold text-white">
                {user.nickname?.charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              {editingNickname ? (
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={nickname}
                    onChange={(e) => setNickname(e.target.value)}
                    className="flex-1 bg-overlay/10 border border-divider/20 rounded-lg px-3 py-1.5 text-sm text-fg focus:outline-none focus:border-primary-500"
                    maxLength={20}
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleSaveNickname();
                      if (e.key === "Escape") {
                        setNickname(user.nickname || "");
                        setEditingNickname(false);
                      }
                    }}
                  />
                  <button
                    onClick={handleSaveNickname}
                    disabled={savingNickname}
                    className="px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white text-sm rounded-lg transition disabled:opacity-50"
                  >
                    {savingNickname ? "..." : "저장"}
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="text-lg font-semibold text-fg">{user.nickname}</span>
                  <button
                    onClick={() => setEditingNickname(true)}
                    className="p-1 text-fg/40 hover:text-fg/70 transition"
                    title="닉네임 수정"
                  >
                    <Pencil className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
              <p className="text-sm text-fg/50 truncate">{user.email}</p>
            </div>
          </div>
        </Section>

        {/* MBTI Section */}
        <Section title="MBTI 설정">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {user.mbti ? (
                <span
                  className={`px-3 py-1.5 rounded-lg text-sm font-bold text-white ${getMBTIColor(user.mbti as MBTIType)}`}
                >
                  {user.mbti}
                </span>
              ) : (
                <span className="text-sm text-fg/50">미설정</span>
              )}
              <span className="text-sm text-fg/60">
                {user.mbti ? "MBTI 기반 추천이 활성화되어 있어요" : "설정하면 성격에 맞는 영화를 추천받을 수 있어요"}
              </span>
            </div>
            <button
              onClick={() => setMbtiModalOpen(true)}
              className="px-3 py-1.5 text-sm text-primary-400 hover:bg-overlay/10 rounded-lg transition"
            >
              {user.mbti ? "변경" : "설정"}
            </button>
          </div>
        </Section>

        {/* Genre Section */}
        <Section title="선호 장르" subtitle="3개 이상 선택해주세요">
          <div className="grid grid-cols-5 gap-2 mb-3">
            {GENRE_OPTIONS.map((genre) => {
              const selected = selectedGenres.includes(genre);
              return (
                <button
                  key={genre}
                  onClick={() => toggleGenre(genre)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                    selected
                      ? "bg-primary-600 text-white ring-1 ring-primary-400/50"
                      : "bg-overlay/10 text-fg/70 hover:bg-overlay/15"
                  }`}
                >
                  {genre}
                </button>
              );
            })}
          </div>
          {genresChanged && (
            <div className="flex items-center gap-2">
              <button
                onClick={handleSaveGenres}
                disabled={savingGenres || selectedGenres.length < 3}
                className="px-4 py-1.5 bg-primary-600 hover:bg-primary-700 text-white text-sm rounded-lg transition disabled:opacity-50"
              >
                {savingGenres ? "저장 중..." : "장르 저장"}
              </button>
              {genresSaved && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-sm text-green-400 flex items-center gap-1"
                >
                  <Check className="w-4 h-4" /> 저장됨
                </motion.span>
              )}
            </div>
          )}
        </Section>

        {/* Theme Section */}
        <Section title="화면 설정">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {theme === "dark" ? (
                <Moon className="w-5 h-5 text-fg/60" />
              ) : (
                <Sun className="w-5 h-5 text-yellow-500" />
              )}
              <span className="text-sm text-fg/80">
                {theme === "dark" ? "다크 모드" : "라이트 모드"}
              </span>
            </div>
            <button
              onClick={toggleTheme}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                theme === "light" ? "bg-primary-500" : "bg-overlay/20"
              }`}
            >
              <span
                className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
                  theme === "light" ? "translate-x-6" : "translate-x-0.5"
                }`}
              />
            </button>
          </div>
        </Section>

        {/* Quick Links */}
        <Section title="바로가기">
          <div className="space-y-1">
            <QuickLink href="/favorites" icon={Heart} label="찜 목록" />
            <QuickLink href="/ratings" icon={Star} label="내 평점" />
            <QuickLink href="/profile" icon={UserIcon} label="프로필" />
          </div>
        </Section>

        {/* Account Section */}
        <Section title="계정 관리">
          <div className="space-y-2">
            <button
              onClick={handleLogout}
              className="flex items-center gap-2.5 w-full px-4 py-3 text-sm text-fg/70 hover:bg-overlay/10 rounded-lg transition"
            >
              <LogOut className="w-4 h-4" />
              <span>로그아웃</span>
            </button>
            <button
              onClick={() => setDeleteConfirmOpen(true)}
              className="flex items-center gap-2.5 w-full px-4 py-3 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition"
            >
              <Trash2 className="w-4 h-4" />
              <span>계정 삭제</span>
            </button>
          </div>
        </Section>
      </div>

      {/* MBTI Modal */}
      {mbtiModalOpen && <MBTIModal onClose={() => { setMbtiModalOpen(false); fetchUser(); }} />}

      {/* Delete Confirm Modal */}
      {deleteConfirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80">
          <div className="w-full max-w-sm bg-surface-card rounded-xl p-6">
            <h3 className="text-lg font-bold text-fg mb-2">계정 삭제</h3>
            <p className="text-sm text-fg/60 mb-6">
              정말 계정을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteConfirmOpen(false)}
                className="flex-1 px-4 py-2.5 bg-overlay/10 text-fg/80 rounded-lg text-sm hover:bg-overlay/20 transition"
              >
                취소
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deleting}
                className="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 transition disabled:opacity-50"
              >
                {deleting ? "삭제 중..." : "삭제"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Section({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <section className="mb-6 bg-surface-card rounded-xl p-5 border border-divider/10">
      <div className="flex items-baseline gap-2 mb-4">
        <h2 className="text-base font-semibold text-fg">{title}</h2>
        {subtitle && <span className="text-xs text-fg/40">{subtitle}</span>}
      </div>
      {children}
    </section>
  );
}

function QuickLink({ href, icon: Icon, label }: { href: string; icon: typeof Heart; label: string }) {
  return (
    <Link
      href={href}
      className="flex items-center justify-between px-4 py-3 text-sm text-fg/70 hover:bg-overlay/10 rounded-lg transition"
    >
      <div className="flex items-center gap-2.5">
        <Icon className="w-4 h-4" />
        <span>{label}</span>
      </div>
      <ChevronRight className="w-4 h-4 text-fg/30" />
    </Link>
  );
}
