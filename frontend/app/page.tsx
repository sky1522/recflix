"use client";

import { useEffect, useState } from "react";
import MovieRow from "@/components/movie/MovieRow";
import HybridMovieRow from "@/components/movie/HybridMovieRow";
import FeaturedBanner from "@/components/movie/FeaturedBanner";
import WeatherBanner from "@/components/weather/WeatherBanner";
import { MovieRowSkeleton, FeaturedBannerSkeleton } from "@/components/ui/Skeleton";
import { getHomeRecommendations } from "@/lib/api";
import { useWeather } from "@/hooks/useWeather";
import { useAuthStore } from "@/stores/authStore";
import type { HomeRecommendations, WeatherType } from "@/types";

export default function HomePage() {
  const [recommendations, setRecommendations] = useState<HomeRecommendations | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { isAuthenticated, user } = useAuthStore();

  const {
    weather,
    loading: weatherLoading,
    setManualWeather,
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

  // Fetch recommendations when weather changes
  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!weather) return;

      setLoading(true);
      try {
        const data = await getHomeRecommendations(weather.condition);
        setRecommendations(data);
        setError(null);
      } catch (err) {
        setError("Failed to load recommendations");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [weather]);

  const handleWeatherChange = (condition: WeatherType) => {
    setManualWeather(condition);
  };

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
      {/* Weather Banner */}
      {weather && (
        <div className="px-4 md:px-8 lg:px-12 pt-2 md:pt-4">
          <WeatherBanner
            weather={weather}
            onWeatherChange={handleWeatherChange}
            showSelector={true}
          />
        </div>
      )}

      {/* Featured Banner */}
      {loading ? (
        <div className="mt-6">
          <FeaturedBannerSkeleton />
        </div>
      ) : recommendations?.featured ? (
        <div className="mt-6">
          <FeaturedBanner movie={recommendations.featured} />
        </div>
      ) : null}

      {/* Loading overlay for recommendations */}
      {loading && recommendations && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-white"></div>
        </div>
      )}

      {/* Main Content */}
      <div className="space-y-8 px-4 md:px-8 lg:px-12 -mt-32 relative z-10">
        {/* === HYBRID RECOMMENDATION (Personalized - Top Priority) === */}
        {recommendations?.hybrid_row && (
          <HybridMovieRow
            title={recommendations.hybrid_row.title}
            description={recommendations.hybrid_row.description}
            movies={recommendations.hybrid_row.movies}
          />
        )}

        {/* Login prompt if not authenticated */}
        {!isAuthenticated && !loading && (
          <div className="p-6 rounded-lg bg-gradient-to-r from-primary-600/20 to-purple-600/20 border border-primary-500/30">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-bold text-white mb-1">
                  더 정확한 추천을 받아보세요
                </h3>
                <p className="text-white/60 text-sm">
                  로그인하고 MBTI를 설정하면 당신의 성향과 오늘 날씨를 모두 고려한 맞춤 추천을 받을 수 있어요.
                </p>
              </div>
              <a
                href="/login"
                className="px-6 py-2.5 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition whitespace-nowrap"
              >
                로그인하기
              </a>
            </div>
          </div>
        )}

        {/* MBTI prompt if authenticated but no MBTI */}
        {isAuthenticated && !user?.mbti && !loading && (
          <div className="p-6 rounded-lg bg-gradient-to-r from-purple-600/20 to-pink-600/20 border border-purple-500/30">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-bold text-white mb-1">
                  MBTI를 설정해보세요
                </h3>
                <p className="text-white/60 text-sm">
                  MBTI를 설정하면 당신의 성격 유형에 맞는 영화를 추천받을 수 있어요.
                </p>
              </div>
              <a
                href="/profile"
                className="px-6 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition whitespace-nowrap"
              >
                MBTI 설정
              </a>
            </div>
          </div>
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
            description={row.description}
            movies={row.movies}
          />
        ))}
      </div>
    </div>
  );
}
