"use client";

import { useState, useEffect, useMemo } from "react";
import Image from "next/image";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Cloud } from "lucide-react";
import { getImageUrl } from "@/lib/utils";
import { useAuthStore } from "@/stores/authStore";
import type { Movie } from "@/types";
import MovieModal from "./MovieModal";

// MBTI 유도 문구 배열
const MBTI_MESSAGES = [
  { title: "오늘 날씨엔 어떤 영화가 좋을까요?", desc: "MBTI와 날씨로 맞춤 추천받기" },
  { title: "당신의 MBTI가 원하는 영화는?", desc: "성격에 딱 맞는 영화 찾기" },
  { title: "비 오는 날, INFP는 뭘 볼까?", desc: "MBTI+날씨 조합 추천 받아보기" },
  { title: "오늘 기분에 맞는 영화 추천", desc: "MBTI 기반 맞춤 큐레이션" },
  { title: "당신만을 위한 영화 추천", desc: "MBTI와 날씨가 만나면?" },
];

const LOGIN_MESSAGES = [
  { title: "더 정확한 추천을 원하시나요?", desc: "로그인하고 맞춤 추천받기" },
  { title: "당신의 취향을 알려주세요", desc: "로그인 후 MBTI 설정하기" },
  { title: "영화 취향, 제대로 분석해드릴게요", desc: "로그인하고 시작하기" },
];

interface FeaturedBannerProps {
  movie: Movie;
}

export default function FeaturedBanner({ movie }: FeaturedBannerProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { isAuthenticated, user } = useAuthStore();

  // 랜덤 메시지 선택 (컴포넌트 마운트 시 한 번만)
  const randomMessage = useMemo(() => {
    if (!isAuthenticated) {
      return LOGIN_MESSAGES[Math.floor(Math.random() * LOGIN_MESSAGES.length)];
    }
    if (!user?.mbti) {
      return MBTI_MESSAGES[Math.floor(Math.random() * MBTI_MESSAGES.length)];
    }
    return null;
  }, [isAuthenticated, user?.mbti]);

  const showPrompt = !isAuthenticated || (isAuthenticated && !user?.mbti);

  return (
    <>
      <div className="relative h-[70vh] md:h-[80vh] w-full">
        {/* Background Image */}
        <div className="absolute inset-0">
          <Image
            src={getImageUrl(movie.poster_path, "original")}
            alt={movie.title_ko || movie.title}
            fill
            className="object-cover"
            priority
          />
          {/* Gradient Overlays */}
          <div className="absolute inset-0 bg-gradient-to-r from-dark-200 via-dark-200/60 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-t from-dark-200 via-transparent to-dark-200/30" />
        </div>

        {/* Content */}
        <div className="absolute bottom-0 left-0 right-0 p-8 md:p-12 lg:p-16">
          <div className="max-w-2xl flex flex-col gap-4">
            {/* MBTI/Login Prompt - 영화 제목 위에 배치 */}
            <AnimatePresence>
              {showPrompt && randomMessage && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                >
                  <Link
                    href={isAuthenticated ? "/profile" : "/login"}
                    className="inline-flex items-center gap-3 px-4 py-2.5 bg-white/10 hover:bg-white/20 backdrop-blur-md rounded-full border border-white/20 transition-all duration-300 group"
                  >
                    <div className="flex items-center justify-center w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full">
                      {isAuthenticated ? (
                        <Sparkles className="w-4 h-4 text-white" />
                      ) : (
                        <Cloud className="w-4 h-4 text-white" />
                      )}
                    </div>
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-white group-hover:text-white/90">
                        {randomMessage.title}
                      </span>
                      <span className="text-xs text-white/60 group-hover:text-white/70">
                        {randomMessage.desc}
                      </span>
                    </div>
                    <svg
                      className="w-4 h-4 text-white/50 group-hover:text-white/80 group-hover:translate-x-1 transition-all"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </Link>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Movie Title */}
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white">
              {movie.title_ko || movie.title}
            </h1>

            {/* Meta Info */}
            <div className="flex items-center space-x-4 text-white/80">
              <div className="flex items-center space-x-1">
                <svg className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                <span className="font-medium">{movie.vote_average.toFixed(1)}</span>
              </div>
              {movie.release_date && (
                <span>{new Date(movie.release_date).getFullYear()}</span>
              )}
              {movie.genres.length > 0 && (
                <span>{movie.genres.slice(0, 3).map(g => typeof g === 'string' ? g : (g as any)?.name_ko || (g as any)?.name).join(" • ")}</span>
              )}
            </div>

            {/* Buttons */}
            <div className="flex space-x-4 mt-2">
              <button
                onClick={() => setIsModalOpen(true)}
                className="flex items-center space-x-2 bg-white text-black px-6 py-3 rounded-md font-medium hover:bg-white/90 transition"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                </svg>
                <span>상세보기</span>
              </button>
              <button className="flex items-center space-x-2 bg-white/20 text-white px-6 py-3 rounded-md font-medium hover:bg-white/30 transition backdrop-blur-sm">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>내 리스트</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <MovieModal movie={movie} onClose={() => setIsModalOpen(false)} />
      )}
    </>
  );
}
