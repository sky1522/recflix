"use client";

import { useState, useMemo, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Cloud, Plus, Check, Sun, CloudRain, CloudSnow, RotateCcw } from "lucide-react";
import { getImageUrl, formatRuntime } from "@/lib/utils";
import { getCatchphrase } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import { useInteractionStore } from "@/stores/interactionStore";
import type { Movie, Weather, WeatherType, MoodType } from "@/types";
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

// 날씨 관련 설정
const weatherConfig: Record<WeatherType, { icon: React.ReactNode; label: string; color: string }> = {
  sunny: { icon: <Sun className="w-4 h-4" />, label: "맑음", color: "text-yellow-400" },
  rainy: { icon: <CloudRain className="w-4 h-4" />, label: "비", color: "text-blue-400" },
  cloudy: { icon: <Cloud className="w-4 h-4" />, label: "흐림", color: "text-gray-400" },
  snowy: { icon: <CloudSnow className="w-4 h-4" />, label: "눈", color: "text-cyan-300" },
};

// 날씨 섹션 고정 문구
const WEATHER_MESSAGE = "날씨에 따른 영화추천";

// 기분 관련 설정 (2x3 그리드 순서)
const moodConfig: Record<MoodType, { emoji: string; label: string; row: number }> = {
  relaxed: { emoji: "😌", label: "편안한", row: 1 },
  tense: { emoji: "😰", label: "긴장감", row: 1 },
  excited: { emoji: "😆", label: "신나는", row: 1 },
  emotional: { emoji: "💕", label: "감성적", row: 2 },
  imaginative: { emoji: "🔮", label: "상상에빠지고싶은", row: 2 },
  light: { emoji: "😄", label: "가볍게", row: 2 },
};

// 기분 버튼 순서 (2x3 그리드)
const moodRow1: MoodType[] = ["relaxed", "tense", "excited"];
const moodRow2: MoodType[] = ["emotional", "imaginative", "light"];

// 기분 섹션 고정 문구
const MOOD_MESSAGE = "지금 기분이 어떠세요?";

interface FeaturedBannerProps {
  movie: Movie;
  weather?: Weather | null;
  onWeatherChange?: (condition: WeatherType) => void;
  isManualWeather?: boolean;
  onResetWeather?: () => void;
  mood?: MoodType | null;
  onMoodChange?: (mood: MoodType | null) => void;
}

export default function FeaturedBanner({
  movie,
  weather,
  onWeatherChange,
  isManualWeather = false,
  onResetWeather,
  mood,
  onMoodChange,
}: FeaturedBannerProps) {
  const router = useRouter();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isAddingToList, setIsAddingToList] = useState(false);
  const { isAuthenticated, user } = useAuthStore();
  const { interactions, fetchInteraction, toggleFavorite } = useInteractionStore();

  const interaction = interactions[movie.id];
  const isFavorited = interaction?.is_favorited ?? false;
  const [catchphrase, setCatchphrase] = useState<string | null>(null);

  // Fetch interaction when authenticated
  useEffect(() => {
    if (isAuthenticated && movie.id) {
      fetchInteraction(movie.id);
    }
  }, [isAuthenticated, movie.id, fetchInteraction]);

  // Fetch LLM catchphrase
  useEffect(() => {
    setCatchphrase(null);
    getCatchphrase(movie.id)
      .then((data) => setCatchphrase(data.catchphrase))
      .catch(() => {});
  }, [movie.id]);

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

  const handleAddToList = async () => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }

    setIsAddingToList(true);
    try {
      await toggleFavorite(movie.id);
    } catch (error) {
      console.error("Failed to toggle favorite:", error);
    } finally {
      setIsAddingToList(false);
    }
  };

  return (
    <>
      <div className="relative h-[50vh] md:h-[55vh] lg:h-[60vh] w-full mb-4 md:mb-6">
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
          <div className="absolute inset-0 bg-gradient-to-r from-dark-200 via-dark-200/70 to-dark-200/30" />
          <div className="absolute inset-0 bg-gradient-to-t from-dark-200 via-transparent to-dark-200/50" />
          <div className="absolute inset-0 bg-gradient-to-b from-dark-200/60 via-transparent to-dark-200" />
        </div>

        {/* Content Container - 하단 영화 정보 */}
        <div className="absolute inset-0 flex flex-col justify-end p-6 md:p-10 lg:p-12">
          {/* 하단 좌측: 영화 정보 */}
          <motion.div
            className="max-w-[85vw] md:max-w-xl lg:max-w-2xl flex flex-col gap-2 md:gap-3 pb-4 md:pb-6"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            {/* Title - 한국어 + 영어 한 줄 */}
            <div className="flex items-baseline gap-2 md:gap-3 min-w-0">
              <h1 className="text-2xl md:text-4xl lg:text-5xl font-bold text-white leading-tight shrink-0 max-w-[70%] truncate">
                {movie.title_ko || movie.title}
              </h1>
              {movie.title_ko && movie.title && movie.title !== movie.title_ko && (
                <span className="text-sm md:text-lg lg:text-xl text-white/40 truncate">
                  {movie.title}
                </span>
              )}
            </div>

            {/* LLM Catchphrase */}
            {catchphrase && (
              <p className="text-sm md:text-base text-white/70 italic truncate">
                &ldquo;{catchphrase}&rdquo;
              </p>
            )}

            {/* Meta Info - 평점, 년도, 러닝타임, 등급 한 줄 */}
            <div className="flex flex-wrap items-center gap-2 md:gap-3 text-sm md:text-base text-white/80">
              <div className="flex items-center space-x-1">
                <svg className="w-4 h-4 md:w-5 md:h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                <span className="font-medium">{movie.vote_average.toFixed(1)}</span>
                <span className="text-white/40 text-xs">({movie.vote_count.toLocaleString()})</span>
              </div>
              {movie.release_date && (
                <>
                  <span className="text-white/30">|</span>
                  <span>{new Date(movie.release_date).getFullYear()}</span>
                </>
              )}
              {movie.runtime && (
                <>
                  <span className="text-white/30">|</span>
                  <span>{formatRuntime(movie.runtime)}</span>
                </>
              )}
              {movie.certification && (
                <span className={`px-1.5 py-0.5 rounded text-xs font-medium border ${
                  ["ALL", "G"].includes(movie.certification.toUpperCase())
                    ? "border-green-500/50 text-green-400"
                    : ["PG", "12", "12+"].includes(movie.certification.toUpperCase())
                    ? "border-blue-500/50 text-blue-400"
                    : ["PG-13", "15", "15+"].includes(movie.certification.toUpperCase())
                    ? "border-yellow-500/50 text-yellow-400"
                    : ["R", "18", "18+", "19", "19+", "NC-17"].includes(movie.certification.toUpperCase())
                    ? "border-red-500/50 text-red-400"
                    : "border-white/30 text-white/60"
                }`}>
                  {movie.certification}
                </span>
              )}
            </div>

            {/* Genre Tags */}
            {movie.genres.length > 0 && (
              <div className="flex flex-wrap gap-1.5 md:gap-2">
                {movie.genres.slice(0, 5).map((genre, i) => (
                  <span
                    key={i}
                    className="px-2 md:px-2.5 py-0.5 md:py-1 bg-white/10 backdrop-blur-sm rounded-full text-xs md:text-sm text-white/80"
                  >
                    {typeof genre === "string" ? genre : (genre as any)?.name_ko || (genre as any)?.name}
                  </span>
                ))}
              </div>
            )}

            {/* Buttons */}
            <div className="flex space-x-3 mt-1">
              <button
                onClick={() => setIsModalOpen(true)}
                className="flex items-center space-x-2 bg-white text-black px-4 md:px-6 py-2.5 md:py-3 rounded-md font-medium hover:bg-white/90 transition text-sm md:text-base"
              >
                <svg className="w-4 h-4 md:w-5 md:h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                </svg>
                <span>상세보기</span>
              </button>
              <button
                onClick={handleAddToList}
                disabled={isAddingToList}
                className={`flex items-center space-x-2 px-4 md:px-6 py-2.5 md:py-3 rounded-md font-medium transition text-sm md:text-base ${
                  isFavorited
                    ? "bg-primary-600 text-white hover:bg-primary-700"
                    : "bg-white/20 text-white hover:bg-white/30 backdrop-blur-sm"
                } ${isAddingToList ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                {isAddingToList ? (
                  <div className="w-4 h-4 md:w-5 md:h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                ) : isFavorited ? (
                  <Check className="w-4 h-4 md:w-5 md:h-5" />
                ) : (
                  <Plus className="w-4 h-4 md:w-5 md:h-5" />
                )}
                <span>{isFavorited ? "내 리스트에 추가됨" : "내 리스트"}</span>
              </button>
            </div>
          </motion.div>
        </div>
      </div>

      {/* 우측 고정 유도 섹션: 스크롤 시에도 따라다님 */}
      <div className="fixed top-[72px] right-4 md:right-8 lg:right-12 z-40 flex flex-col items-end gap-2">
        {/* MBTI 유도 섹션 */}
        <AnimatePresence>
          {showPrompt && randomMessage && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="w-80"
            >
              <Link
                href={isAuthenticated ? "/profile" : "/login"}
                className="flex items-center gap-3 w-full px-4 py-2.5 bg-black/40 hover:bg-black/60 backdrop-blur-md rounded-2xl border border-white/20 transition-all duration-300 group"
              >
                <div className="flex items-center justify-center w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex-shrink-0">
                  {isAuthenticated ? (
                    <Sparkles className="w-4 h-4 text-white" />
                  ) : (
                    <Cloud className="w-4 h-4 text-white" />
                  )}
                </div>
                <div className="flex flex-col flex-1 min-w-0">
                  <span className="text-sm font-medium text-white group-hover:text-white/90 truncate">
                    {randomMessage.title}
                  </span>
                  <span className="text-xs text-white/60 group-hover:text-white/70 truncate">
                    {randomMessage.desc}
                  </span>
                </div>
                <svg
                  className="w-4 h-4 text-white/50 group-hover:text-white/80 group-hover:translate-x-1 transition-all flex-shrink-0"
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

        {/* 날씨 섹션 */}
        {weather && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="w-80 flex flex-col gap-1.5 px-4 py-2.5 bg-black/40 backdrop-blur-md rounded-2xl border border-white/20"
          >
            <div className="text-xs text-white/70 text-center">
              {WEATHER_MESSAGE}
            </div>
            <div className="flex items-center justify-center gap-2">
              <div className={`flex items-center gap-1.5 ${weatherConfig[weather.condition].color}`}>
                {weatherConfig[weather.condition].icon}
                <span className="text-sm font-medium text-white">
                  {weather.temperature}°C
                </span>
              </div>
              <div className="w-px h-4 bg-white/20" />
              <div className="flex items-center gap-1">
                {(["sunny", "rainy", "cloudy", "snowy"] as WeatherType[]).map((w) => (
                  <button
                    key={w}
                    onClick={() => onWeatherChange?.(w)}
                    className={`p-1.5 rounded-full transition-all ${
                      weather.condition === w
                        ? "bg-white/25 scale-110"
                        : "hover:bg-white/15"
                    } ${weatherConfig[w].color}`}
                    title={weatherConfig[w].label}
                  >
                    {weatherConfig[w].icon}
                  </button>
                ))}
              </div>
              {isManualWeather && onResetWeather && (
                <>
                  <div className="w-px h-4 bg-white/20" />
                  <button
                    onClick={onResetWeather}
                    className="p-1.5 rounded-full transition-all hover:bg-white/15 text-white/70 hover:text-white"
                    title="실시간 날씨로 복귀"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                </>
              )}
            </div>
          </motion.div>
        )}

        {/* 기분 섹션 (2x3 그리드) */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="w-80 flex flex-col gap-1.5 px-4 py-2.5 bg-black/40 backdrop-blur-md rounded-2xl border border-white/20"
        >
          <div className="text-xs text-white/70 text-center">
            {MOOD_MESSAGE}
          </div>
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-center gap-1">
              {moodRow1.map((m) => (
                <button
                  key={m}
                  onClick={() => onMoodChange?.(mood === m ? null : m)}
                  className={`px-2 py-1 rounded-full text-xs transition-all whitespace-nowrap ${
                    mood === m
                      ? "bg-white/25 scale-105"
                      : "hover:bg-white/15"
                  }`}
                  title={moodConfig[m].label}
                >
                  <span>{moodConfig[m].emoji}</span>
                  <span className="ml-0.5 text-white/90 hidden sm:inline">{moodConfig[m].label}</span>
                </button>
              ))}
            </div>
            <div className="flex items-center justify-center gap-1">
              {moodRow2.map((m) => (
                <button
                  key={m}
                  onClick={() => onMoodChange?.(mood === m ? null : m)}
                  className={`px-2 py-1 rounded-full text-xs transition-all whitespace-nowrap ${
                    mood === m
                      ? "bg-white/25 scale-105"
                      : "hover:bg-white/15"
                  }`}
                  title={moodConfig[m].label}
                >
                  <span>{moodConfig[m].emoji}</span>
                  <span className="ml-0.5 text-white/90 hidden sm:inline">{moodConfig[m].label}</span>
                </button>
              ))}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <MovieModal movie={movie} onClose={() => setIsModalOpen(false)} />
      )}
    </>
  );
}
