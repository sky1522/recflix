"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import MovieRow from "@/components/movie/MovieRow";
import HybridMovieRow from "@/components/movie/HybridMovieRow";
import FeaturedBanner from "@/components/movie/FeaturedBanner";
import { MovieRowSkeleton, FeaturedBannerSkeleton } from "@/components/ui/Skeleton";
import { getHomeRecommendations, getMovies } from "@/lib/api";
import { useWeather } from "@/hooks/useWeather";
import { useAuthStore } from "@/stores/authStore";
import { useMoodStore } from "@/stores/useMoodStore";
import type { HomeRecommendations, Movie } from "@/types";
import {
  MOOD_SUBTITLES,
  MBTI_SUBTITLES,
  FIXED_SUBTITLES,
  getSubtitle,
  getHybridContextSubtitle,
  getWeatherContextSubtitle,
} from "@/lib/curationMessages";
import { buildUserContext, type UserContext } from "@/lib/contextCuration";
import { SUBTITLE_COUNT, WEATHER_THEME_CLASSES } from "@/lib/constants";

/** 추천 Row 타이틀에서 섹션 이름 추출 (이벤트 트래킹용) */
function getSectionFromTitle(title: string): string {
  if (title.includes("인기 영화")) return "popular";
  if (title.includes("높은 평점")) return "top_rated";
  if (title.includes("성향 추천")) return "mbti";
  if (
    title.includes("맑은") ||
    title.includes("비 오는") ||
    title.includes("흐린") ||
    title.includes("눈 오는")
  ) return "weather";
  return "mood";
}

// Module-level cache: survives component remounts (back navigation)
let cachedRecommendations: HomeRecommendations | null = null;
let cachedKey = "";

export default function HomePage() {
  const [recommendations, setRecommendations] = useState<HomeRecommendations | null>(cachedRecommendations);
  const [loading, setLoading] = useState(!cachedRecommendations);
  const [error, setError] = useState<string | null>(null);
  const [subtitleIdx, setSubtitleIdx] = useState(0);
  const [userContext, setUserContext] = useState<UserContext | null>(null);

  const [koreanMovies, setKoreanMovies] = useState<Movie[]>([]);

  const { isAuthenticated, user } = useAuthStore();
  const { mood } = useMoodStore();
  const prevAuthRef = useRef(isAuthenticated);

  // Guest MBTI: localStorage에서 읽고, 헤더 변경 시 즉시 반영
  const [guestMBTI, setGuestMBTI] = useState<string | null>(null);
  useEffect(() => {
    setGuestMBTI(localStorage.getItem("guest_mbti"));
    const handleGuestMBTIChange = (e: Event) => {
      setGuestMBTI((e as CustomEvent).detail);
    };
    window.addEventListener("guest_mbti_change", handleGuestMBTIChange);
    return () => window.removeEventListener("guest_mbti_change", handleGuestMBTIChange);
  }, []);

  // Track interaction version to invalidate cache on rating/favorite changes
  const [interactionVersion, setInteractionVersion] = useState(0);
  useEffect(() => {
    // Read initial value
    const readVersion = () => {
      const v = parseInt(localStorage.getItem("interaction_version") || "0", 10);
      setInteractionVersion(v);
    };
    readVersion();
    // Re-check when user returns to page (tab switch, back navigation)
    window.addEventListener("focus", readVersion);
    return () => window.removeEventListener("focus", readVersion);
  }, []);

  // 페이지 로드 시 랜덤 서브타이틀 인덱스 결정 (하이드레이션 안전)
  useEffect(() => {
    setSubtitleIdx(Math.floor(Math.random() * SUBTITLE_COUNT));
  }, []);

  // 로그아웃 감지 시 즉시 추천 데이터 초기화 (캐시 포함)
  useEffect(() => {
    if (prevAuthRef.current && !isAuthenticated) {
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
  } = useWeather({ autoFetch: true });

  // Apply weather theme to body
  useEffect(() => {
    if (weather) {
      document.body.classList.remove(...WEATHER_THEME_CLASSES);
      document.body.classList.add(`theme-${weather.condition}`);
    }

    return () => {
      document.body.classList.remove(...WEATHER_THEME_CLASSES);
    };
  }, [weather]);

  // 컨텍스트 감지: weather 데이터에서 기온 활용
  useEffect(() => {
    const temp = weather?.temperature ?? 15;
    const condition = weather?.condition ?? 'sunny';
    setUserContext(buildUserContext(temp, condition));
  }, [weather]);

  // Fetch Korean popular movies (independent, one-time)
  useEffect(() => {
    getMovies({ country: "대한민국", sort_by: "popularity", page_size: 40 })
      .then((res) => setKoreanMovies(res.items))
      .catch((err) => console.error("Failed to fetch Korean movies:", err));
  }, []);

  // Fetch recommendations when weather, mood, auth state, or interaction changes
  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!weather) return;

      const iv = typeof window !== "undefined"
        ? localStorage.getItem("interaction_version") || "0"
        : "0";
      const effectiveMBTI = isAuthenticated ? user?.mbti : guestMBTI;
      const key = `${weather.condition}-${mood}-${user?.id || 'anon'}-${effectiveMBTI || 'none'}-iv${iv}`;

      // Use cache if params haven't changed (e.g. back navigation)
      if (cachedRecommendations && cachedKey === key) {
        setRecommendations(cachedRecommendations);
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const mbtiParam = isAuthenticated ? undefined : guestMBTI;
        const data = await getHomeRecommendations(weather.condition, mood, mbtiParam);
        setRecommendations(data);
        setError(null);
        // Update module-level cache
        cachedRecommendations = data;
        cachedKey = key;
      } catch (err) {
        setError("Failed to load recommendations");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [weather, mood, isAuthenticated, user?.id, user?.mbti, guestMBTI, interactionVersion]);

  // Featured movie 선택 로직:
  // 로그인 시 -> hybrid_row 첫 번째 영화 (맞춤 추천)
  // 비로그인 -> rows[0] 첫 번째 영화 (인기 영화)
  const featuredMovie: Movie | null = useMemo(() => {
    if (!recommendations) return null;

    const hybridMovies = recommendations.hybrid_row?.movies;
    if (isAuthenticated && hybridMovies && hybridMovies.length > 0) {
      return hybridMovies[0];
    }

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
    if (title.includes("성향 추천")) {
      const mbtiMatch = title.match(/([A-Z]{4})/);
      if (mbtiMatch && MBTI_SUBTITLES[mbtiMatch[1]]) {
        return getSubtitle(MBTI_SUBTITLES[mbtiMatch[1]], subtitleIdx);
      }
    }
    if (
      title.includes("맑은") ||
      title.includes("비 오는") ||
      title.includes("흐린") ||
      title.includes("눈 오는")
    ) {
      if (userContext) {
        return getWeatherContextSubtitle(userContext.season, userContext.tempRange, subtitleIdx);
      }
      return '';
    }
    for (const key of Object.keys(MOOD_SUBTITLES)) {
      if (
        (key === "relaxed" && title.includes("편안한")) ||
        (key === "tense" && title.includes("긴장감")) ||
        (key === "energetic" && title.includes("신나는")) ||
        (key === "romantic" && title.includes("감성적")) ||
        (key === "imaginative" && title.includes("상상에")) ||
        (key === "light" && title.includes("가볍게")) ||
        (key === "gloomy" && title.includes("울적한")) ||
        (key === "stifled" && title.includes("답답"))
      ) return getSubtitle(MOOD_SUBTITLES[key], subtitleIdx);
    }
    return '';
  };

  const getHybridSubtitle = (): string => {
    if (userContext) {
      return getHybridContextSubtitle(userContext.timeOfDay, subtitleIdx);
    }
    return '';
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
      {/* Featured Banner */}
      {loading ? (
        <div className="mt-2 md:mt-4">
          <FeaturedBannerSkeleton />
        </div>
      ) : featuredMovie ? (
        <div className="mt-2 md:mt-4">
          <FeaturedBanner movie={featuredMovie} />
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
            section="personal"
            requestId={recommendations.request_id}
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
            section={getSectionFromTitle(row.title)}
            requestId={recommendations.request_id}
          />
        ))}

        {/* Korean Popular Movies */}
        {koreanMovies.length > 0 && (
          <MovieRow
            title="🇰🇷 한국 인기 영화"
            subtitle="지금 한국에서 사랑받는 영화들"
            movies={koreanMovies}
            section="korean_popular"
          />
        )}
      </div>
    </div>
  );
}
