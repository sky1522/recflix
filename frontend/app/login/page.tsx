"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Eye, EyeOff, Mail, Lock, X } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      await login({ email, password });
      router.push("/");
    } catch (err: any) {
      setError(err.message || "로그인에 실패했습니다.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8 bg-dark-200">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-6 md:mb-8">
          <Link href="/" className="text-3xl md:text-4xl font-bold text-primary-500">
            RecFlix
          </Link>
          <p className="text-white/60 mt-2 text-sm md:text-base">맞춤형 영화 추천 플랫폼</p>
        </div>

        {/* Login Form */}
        <div className="relative bg-dark-100 rounded-xl p-6 md:p-8 shadow-xl">
          <button
            onClick={() => router.back()}
            className="absolute top-4 right-4 p-1.5 text-white/40 hover:text-white hover:bg-white/10 rounded-full transition"
          >
            <X className="w-5 h-5" />
          </button>
          <h1 className="text-xl md:text-2xl font-bold text-white mb-6">로그인</h1>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-500 text-sm"
            >
              {error}
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white/80 mb-1.5">
                이메일
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-dark-200 border border-white/10 rounded-lg text-white placeholder-white/40 focus:outline-none focus:border-primary-500 transition text-base"
                  placeholder="your@email.com"
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white/80 mb-1.5">
                비밀번호
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-12 py-3 bg-dark-200 border border-white/10 rounded-lg text-white placeholder-white/40 focus:outline-none focus:border-primary-500 transition text-base"
                  placeholder="••••••••"
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-white/40 hover:text-white/60 transition"
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 bg-primary-600 hover:bg-primary-700 active:bg-primary-800 disabled:bg-primary-800 disabled:cursor-not-allowed text-white font-medium rounded-lg transition flex items-center justify-center space-x-2"
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>로그인 중...</span>
                </>
              ) : (
                <span>로그인</span>
              )}
            </button>
          </form>

          <div className="mt-6 text-center text-white/60 text-sm md:text-base">
            계정이 없으신가요?{" "}
            <Link href="/signup" className="text-primary-500 hover:text-primary-400 transition font-medium">
              회원가입
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
