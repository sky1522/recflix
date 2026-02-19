"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Star, Users } from "lucide-react";
import { getMovie, getSimilarMovies, getCatchphrase } from "@/lib/api";
import { useInteractionStore } from "@/stores/interactionStore";
import { useAuthStore } from "@/stores/authStore";
import type { MovieDetail, Movie } from "@/types";
import MovieHero from "./components/MovieHero";
import MovieSidebar from "./components/MovieSidebar";
import SimilarMovies from "./components/SimilarMovies";
import MovieDetailSkeleton from "./components/MovieDetailSkeleton";

export default function MovieDetailPage() {
  const params = useParams();
  const router = useRouter();
  const movieId = Number(params.id);

  const [movie, setMovie] = useState<MovieDetail | null>(null);
  const [similar, setSimilar] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ratingHover, setRatingHover] = useState(0);
  const [catchphrase, setCatchphrase] = useState<string | null>(null);
  const [catchphraseLoading, setCatchphraseLoading] = useState(false);

  const { isAuthenticated } = useAuthStore();
  const { interactions, fetchInteraction, toggleFavorite, setRating } =
    useInteractionStore();
  const interaction = interactions[movieId];

  useEffect(() => {
    const fetchData = async () => {
      if (!movieId || isNaN(movieId)) {
        setError("Invalid movie ID");
        setLoading(false);
        return;
      }

      setLoading(true);
      setCatchphrase(null);
      try {
        const [movieData, similarData] = await Promise.all([
          getMovie(movieId),
          getSimilarMovies(movieId, 12),
        ]);
        setMovie(movieData);
        setSimilar(similarData);

        // 캐치프레이즈는 영화 데이터 로드 후 별도로 요청 (비동기)
        setCatchphraseLoading(true);
        getCatchphrase(movieId)
          .then((res) => setCatchphrase(res.catchphrase))
          .catch(() => setCatchphrase(movieData.tagline || null))
          .finally(() => setCatchphraseLoading(false));

        if (isAuthenticated) {
          await fetchInteraction(movieId);
        }
      } catch (err) {
        console.error("Failed to fetch movie:", err);
        setError("영화 정보를 불러오는데 실패했습니다.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [movieId, isAuthenticated, fetchInteraction]);

  const handleFavoriteClick = async () => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    try {
      await toggleFavorite(movieId);
    } catch (error) {
      console.error("Failed to toggle favorite:", error);
    }
  };

  const handleRatingClick = async (score: number) => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    try {
      await setRating(movieId, score);
    } catch (error) {
      console.error("Failed to set rating:", error);
    }
  };

  const isFavorited = interaction?.is_favorited ?? false;
  const userRating = interaction?.rating ?? 0;
  const displayRating = ratingHover || userRating;

  if (loading) {
    return <MovieDetailSkeleton />;
  }

  if (error || !movie) {
    return (
      <div className="min-h-screen bg-dark-200 pt-20 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 text-lg mb-4">{error || "영화를 찾을 수 없습니다."}</p>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition"
          >
            뒤로 가기
          </button>
        </div>
      </div>
    );
  }

  const displayTitle = movie.title_ko || movie.title;
  const overview = movie.overview;

  return (
    <div className="min-h-screen bg-dark-200">
      {/* Hero Section */}
      <MovieHero
        movie={movie}
        displayTitle={displayTitle}
        catchphrase={catchphrase}
        catchphraseLoading={catchphraseLoading}
        isFavorited={isFavorited}
        onBack={() => router.back()}
        onFavoriteClick={handleFavoriteClick}
      />

      {/* Content Section */}
      <div className="max-w-7xl mx-auto px-4 md:px-8 lg:px-12 py-8 md:py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 lg:gap-12">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* User Rating */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="p-6 bg-dark-100 rounded-lg"
            >
              <div className="flex items-center gap-4 flex-wrap">
                <h2 className="text-xl font-semibold text-white">내 평점</h2>
                <div className="flex items-center gap-0.5">
                  {[1, 2, 3, 4, 5].map((score) => (
                    <button
                      key={score}
                      onClick={() => handleRatingClick(score)}
                      onMouseEnter={() => setRatingHover(score)}
                      onMouseLeave={() => setRatingHover(0)}
                      className="p-0.5 transition-transform hover:scale-110"
                    >
                      <Star
                        className={`w-7 h-7 transition-colors ${
                          score <= displayRating
                            ? "text-yellow-400 fill-yellow-400"
                            : "text-white/30"
                        }`}
                      />
                    </button>
                  ))}
                </div>
                {userRating > 0 && (
                  <span className="text-xl font-bold text-yellow-400">
                    {userRating.toFixed(1)}
                  </span>
                )}
                {!isAuthenticated && (
                  <Link href="/login" className="text-primary-400 text-sm hover:underline">
                    로그인하고 평점 남기기
                  </Link>
                )}
              </div>
            </motion.section>

            {/* Overview */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <h2 className="text-xl font-semibold text-white mb-4">줄거리</h2>
              <p className="text-white/80 leading-relaxed text-lg">
                {overview || "줄거리 정보가 없습니다."}
              </p>
            </motion.section>

            {/* Cast */}
            {movie.cast_ko && (
              <motion.section
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
              >
                <h2 className="text-xl font-semibold text-white mb-4">출연진</h2>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                  {movie.cast_ko.split(", ").slice(0, 8).map((name) => (
                    <Link
                      key={name}
                      href={`/movies?query=${encodeURIComponent(name)}`}
                      className="flex items-center space-x-3 p-3 bg-dark-100 hover:bg-dark-100/70 rounded-lg transition"
                    >
                      <div className="w-10 h-10 bg-dark-200 rounded-full flex items-center justify-center flex-shrink-0">
                        <Users className="w-5 h-5 text-white/30" />
                      </div>
                      <span className="text-white/80 text-sm truncate">{name}</span>
                    </Link>
                  ))}
                </div>
              </motion.section>
            )}

            {/* Similar Movies */}
            <SimilarMovies similar={similar} />
          </div>

          {/* Sidebar */}
          <MovieSidebar movie={movie} />
        </div>
      </div>
    </div>
  );
}
