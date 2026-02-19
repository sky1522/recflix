"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { X } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import type { MBTIType } from "@/types";

const MBTI_TYPES: MBTIType[] = [
  "INTJ", "INTP", "ENTJ", "ENTP",
  "INFJ", "INFP", "ENFJ", "ENFP",
  "ISTJ", "ISFJ", "ESTJ", "ESFJ",
  "ISTP", "ISFP", "ESTP", "ESFP",
];

export default function SignupPage() {
  const router = useRouter();
  const { signup, isLoading } = useAuthStore();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    nickname: "",
    mbti: "",
  });
  const [error, setError] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (formData.password !== formData.confirmPassword) {
      setError("비밀번호가 일치하지 않습니다.");
      return;
    }

    if (formData.password.length < 6) {
      setError("비밀번호는 6자 이상이어야 합니다.");
      return;
    }

    try {
      await signup({
        email: formData.email,
        password: formData.password,
        nickname: formData.nickname,
        mbti: formData.mbti || undefined,
      });
      router.push("/");
    } catch (err: any) {
      setError(err.message || "회원가입에 실패했습니다.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-dark-200">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="text-4xl font-bold text-primary-500">
            RecFlix
          </Link>
          <p className="text-white/60 mt-2">맞춤형 영화 추천 플랫폼</p>
        </div>

        {/* Signup Form */}
        <div className="relative bg-dark-100 rounded-lg p-8">
          <button
            onClick={() => router.back()}
            className="absolute top-4 right-4 p-1.5 text-white/40 hover:text-white hover:bg-white/10 rounded-full transition"
          >
            <X className="w-5 h-5" />
          </button>
          <h1 className="text-2xl font-bold text-white mb-6">회원가입</h1>

          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-md text-red-500 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white/80 mb-1.5">
                이메일 *
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-2.5 bg-dark-200 border border-white/10 rounded-md text-white placeholder-white/40 focus:outline-none focus:border-primary-500 transition"
                placeholder="your@email.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white/80 mb-1.5">
                닉네임 *
              </label>
              <input
                type="text"
                name="nickname"
                value={formData.nickname}
                onChange={handleChange}
                className="w-full px-4 py-2.5 bg-dark-200 border border-white/10 rounded-md text-white placeholder-white/40 focus:outline-none focus:border-primary-500 transition"
                placeholder="닉네임을 입력하세요"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white/80 mb-1.5">
                비밀번호 *
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="w-full px-4 py-2.5 bg-dark-200 border border-white/10 rounded-md text-white placeholder-white/40 focus:outline-none focus:border-primary-500 transition"
                placeholder="6자 이상"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white/80 mb-1.5">
                비밀번호 확인 *
              </label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                className="w-full px-4 py-2.5 bg-dark-200 border border-white/10 rounded-md text-white placeholder-white/40 focus:outline-none focus:border-primary-500 transition"
                placeholder="비밀번호를 다시 입력"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white/80 mb-1.5">
                MBTI (선택)
              </label>
              <select
                name="mbti"
                value={formData.mbti}
                onChange={handleChange}
                className="w-full px-4 py-2.5 bg-dark-200 border border-white/10 rounded-md text-white focus:outline-none focus:border-primary-500 transition"
              >
                <option value="">선택 안함</option>
                {MBTI_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
              <p className="text-xs text-white/40 mt-1">
                MBTI를 입력하면 더 정확한 추천을 받을 수 있어요!
              </p>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-primary-800 disabled:cursor-not-allowed text-white font-medium rounded-md transition"
            >
              {isLoading ? "가입 중..." : "회원가입"}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/10" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-3 bg-dark-100 text-white/40">또는</span>
            </div>
          </div>

          {/* Social Login */}
          <div className="space-y-3">
            <button
              type="button"
              onClick={() => {
                const clientId = process.env.NEXT_PUBLIC_KAKAO_CLIENT_ID;
                const redirectUri = process.env.NEXT_PUBLIC_KAKAO_REDIRECT_URI;
                if (clientId && redirectUri) {
                  window.location.href = `https://kauth.kakao.com/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code`;
                }
              }}
              className="w-full py-3 bg-[#FEE500] hover:bg-[#FDD835] text-[#191919] font-medium rounded-lg transition flex items-center justify-center gap-2"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M10 3C5.58 3 2 5.79 2 9.21c0 2.17 1.45 4.08 3.63 5.17l-.93 3.42c-.08.29.25.52.51.36l4.09-2.7c.23.02.46.03.7.03 4.42 0 8-2.79 8-6.22S14.42 3 10 3z" fill="#191919"/>
              </svg>
              카카오로 시작하기
            </button>

            <button
              type="button"
              onClick={() => {
                const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
                const redirectUri = process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI;
                if (clientId && redirectUri) {
                  window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=openid%20email%20profile`;
                }
              }}
              className="w-full py-3 bg-white hover:bg-gray-100 text-gray-700 font-medium rounded-lg transition flex items-center justify-center gap-2 border border-white/20"
            >
              <svg width="20" height="20" viewBox="0 0 20 20">
                <path d="M19.6 10.23c0-.68-.06-1.36-.17-2H10v3.8h5.38a4.6 4.6 0 01-2 3.02v2.5h3.24c1.89-1.74 2.98-4.3 2.98-7.32z" fill="#4285F4"/>
                <path d="M10 20c2.7 0 4.96-.9 6.62-2.42l-3.24-2.5c-.9.6-2.04.95-3.38.95-2.6 0-4.8-1.76-5.58-4.12H1.07v2.58A9.99 9.99 0 0010 20z" fill="#34A853"/>
                <path d="M4.42 11.91A6.01 6.01 0 014.1 10c0-.66.11-1.31.32-1.91V5.51H1.07A9.99 9.99 0 000 10c0 1.61.39 3.14 1.07 4.49l3.35-2.58z" fill="#FBBC05"/>
                <path d="M10 3.96c1.47 0 2.78.5 3.82 1.5l2.86-2.86C14.96.99 12.7 0 10 0A9.99 9.99 0 001.07 5.51l3.35 2.58C5.2 5.72 7.4 3.96 10 3.96z" fill="#EA4335"/>
              </svg>
              Google로 시작하기
            </button>
          </div>

          <div className="mt-6 text-center text-white/60">
            이미 계정이 있으신가요?{" "}
            <Link href="/login" className="text-primary-500 hover:text-primary-400 transition">
              로그인
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
