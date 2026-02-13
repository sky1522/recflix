"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import MovieRow from "@/components/movie/MovieRow";
import HybridMovieRow from "@/components/movie/HybridMovieRow";
import FeaturedBanner from "@/components/movie/FeaturedBanner";
import { MovieRowSkeleton, FeaturedBannerSkeleton } from "@/components/ui/Skeleton";
import { getHomeRecommendations } from "@/lib/api";
import { useWeather } from "@/hooks/useWeather";
import { useAuthStore } from "@/stores/authStore";
import type { HomeRecommendations, WeatherType, Movie, Weather, MoodType } from "@/types";
import {
  WEATHER_SUBTITLES,
  MOOD_SUBTITLES,
  MBTI_SUBTITLES,
  FIXED_SUBTITLES,
  getSubtitle,
} from "@/lib/curationMessages";

// Module-level cache: survives component remounts (back navigation)
let cachedRecommendations: HomeRecommendations | null = null;
let cachedKey = "";
let cachedMood: MoodType | null = null;

export default function HomePage() {
  const [recommendations, setRecommendations] = useState<HomeRecommendations | null>(cachedRecommendations);
  const [loading, setLoading] = useState(!cachedRecommendations);
  const [error, setError] = useState<string | null>(null);
  const [mood, setMood] = useState<MoodType | null>(cachedMood);
  const [subtitleIdx, setSubtitleIdx] = useState(0);

  const { isAuthenticated, user } = useAuthStore();
  const prevAuthRef = useRef(isAuthenticated);

  // 페이지 로드 시 랜덤 서브타이틀 인덱스 결정 (하이드레이션 안전)
  useEffect(() => {
    setSubtitleIdx(Math.floor(Math.random() * 3));
  }, []);

  // 로그아웃 감지 시 즉시 추천 데이터 초기화 (캐시 포함)
  useEffect(() => {
    if (prevAuthRef.current && !isAuthenticated) {
      // 로그아웃됨: 이전에 인증됨 -> 현재 미인증
      cachedRecommendations = null;
      cachedKey = "";
      setRecommendations(null);
      setLoading(true);
    }
    prevAuthRef.current = isAuthenticated;
  }, [isAuthenticated]);

  const {
    weather,
    loading: weatherLoading,
    isManual: isManualWeather,
    setManualWeather,
    resetToRealWeather,
  } = useWeather({ autoFetch: true });

  // Apply weather theme to body
  useEffect(() => {
    if (weather) {
      // Remove all theme classes
      document.body.classList.remove(
        "theme-sunny",
        "theme-rainy",
        "theme-cloudy",
        "theme-snowy"
      );
      // Add current theme class
      document.body.classList.add(`theme-${weather.condition}`);
    }

    return () => {
      document.body.classList.remove(
        "theme-sunny",
        "theme-rainy",
        "theme-cloudy",
        "theme-snowy"
      );
    };
  }, [weather]);

  // Fetch recommendations when weather, mood, or auth state changes
  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!weather) return;

      const key = `${weather.condition}-${mood}-${isAuthenticated}`;

      // Use cache if params haven't changed (e.g. back navigation)
      if (cachedRecommendations && cachedKey === key) {
        setRecommendations(cachedRecommendations);
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const data = await getHomeRecommendations(weather.condition, mood);
        setRecommendations(data);
        setError(null);
        // Update module-level cache
        cachedRecommendations = data;
        cachedKey = key;
        cachedMood = mood;
      } catch (err) {
        setError("Failed to load recommendations");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [weather, mood, isAuthenticated]);  // isAuthenticated 추가: 로그인/로그아웃 시 추천 갱신

  const handleWeatherChange = (condition: WeatherType) => {
    setManualWeather(condition);
  };

  // Featured movie 선택 로직:
  // 로그인 시 -> hybrid_row 첫 번째 영화 (맞춤 추천)
  // 비로그인 -> rows[0] 첫 번째 영화 (인기 영화)
  const featuredMovie: Movie | null = useMemo(() => {
    if (!recommendations) return null;

    // 로그인 상태이고 맞춤 추천 영화가 있으면 첫 번째 영화 사용
    const hybridMovies = recommendations.hybrid_row?.movies;
    if (isAuthenticated && hybridMovies && hybridMovies.length > 0) {
      return hybridMovies[0];
    }

    // 비로그인: rows의 첫 번째 섹션(인기 영화)의 첫 번째 영화
    const firstRow = recommendations.rows?.[0];
    if (firstRow?.movies?.length > 0) {
      return firstRow.movies[0];
    }

    return recommendations.featured ?? null;
  }, [isAuthenticated, recommendations]);

  if (weatherLoading && loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-gray-400">날씨 정보를 가져오는 중...</p>
        </div>
      </div>
    );
  }

  // subtitle 결정 함수 (3종 배열에서 subtitleIdx로 선택)
  const getRowSubtitle = (title: string): string => {
    if (title.includes("인기 영화")) return getSubtitle(FIXED_SUBTITLES.popular, subtitleIdx);
    if (title.includes("높은 평점")) return getSubtitle(FIXED_SUBTITLES.topRated, subtitleIdx);
    // MBTI - 타이틀에서 MBTI 유형 직접 추출 (user?.mbti가 null일 수 있으므로)
    if (title.includes("성향 추천")) {
      const mbtiMatch = title.match(/([A-Z]{4})/);
      if (mbtiMatch && MBTI_SUBTITLES[mbtiMatch[1]]) {
        return getSubtitle(MBTI_SUBTITLES[mbtiMatch[1]], subtitleIdx);
      }
    }
    // Weather
    for (const key of Object.keys(WEATHER_SUBTITLES)) {
      if (
        (key === "sunny" && title.includes("맑은")) ||
        (key === "rainy" && title.includes("비 오는")) ||
        (key === "cloudy" && title.includes("흐린")) ||
        (key === "snowy" && title.includes("눈 오는"))
      ) return getSubtitle(WEATHER_SUBTITLES[key], subtitleIdx);
    }
    // Mood
    for (const key of Object.keys(MOOD_SUBTITLES)) {
      if (
        (key === "relaxed" && title.includes("편안한")) ||
        (key === "tense" && title.includes("긴장감")) ||
        (key === "excited" && title.includes("신나는")) ||
        (key === "emotional" && title.includes("감성적")) ||
        (key === "imaginative" && title.includes("상상에")) ||
        (key === "light" && title.includes("가볍게")) ||
        (key === "gloomy" && title.includes("울적한")) ||
        (key === "stifled" && title.includes("답답"))
      ) return getSubtitle(MOOD_SUBTITLES[key], subtitleIdx);
    }
    return '';
  };

  const getHybridSubtitle = (): string => {
    if (mood && MOOD_SUBTITLES[mood]) return getSubtitle(MOOD_SUBTITLES[mood], subtitleIdx);
    const mbti = user?.mbti;
    if (mbti && MBTI_SUBTITLES[mbti]) return getSubtitle(MBTI_SUBTITLES[mbti], subtitleIdx);
    if (weather?.condition && WEATHER_SUBTITLES[weather.condition]) return getSubtitle(WEATHER_SUBTITLES[weather.condition], subtitleIdx);
    return getSubtitle(FIXED_SUBTITLES.hybrid, subtitleIdx);
  };

  if (error && !recommendations) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="pb-24 md:pb-20">
      {/* Featured Banner (includes compact weather bar) */}
      {loading ? (
        <div className="mt-2 md:mt-4">
          <FeaturedBannerSkeleton />
        </div>
      ) : featuredMovie ? (
        <div className="mt-2 md:mt-4">
          <FeaturedBanner
            movie={featuredMovie}
            weather={weather}
            onWeatherChange={handleWeatherChange}
            isManualWeather={isManualWeather}
            onResetWeather={resetToRealWeather}
            mood={mood}
            onMoodChange={setMood}
          />
        </div>
      ) : null}

      {/* Loading overlay for recommendations */}
      {loading && recommendations && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-white"></div>
        </div>
      )}

      {/* Main Content */}
      <div className="space-y-8 px-4 md:px-8 lg:px-12">
        {/* === HYBRID RECOMMENDATION (Personalized - Top Priority) === */}
        {recommendations?.hybrid_row && (
          <HybridMovieRow
            title={recommendations.hybrid_row.title}
            subtitle={getHybridSubtitle()}
            movies={recommendations.hybrid_row.movies}
          />
        )}

        {/* Loading Skeletons */}
        {loading && !recommendations && (
          <>
            <MovieRowSkeleton />
            <MovieRowSkeleton />
            <MovieRowSkeleton />
          </>
        )}

        {/* Regular Recommendation Rows */}
        {recommendations?.rows.map((row, index) => (
          <MovieRow
            key={`${row.title}-${index}`}
            title={row.title}
            subtitle={getRowSubtitle(row.title)}
            movies={row.movies}
          />
        ))}
      </div>
    </div>
  );
}
