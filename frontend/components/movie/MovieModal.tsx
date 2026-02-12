"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { Heart, Star, X } from "lucide-react";
import { getImageUrl, formatRuntime, formatDate } from "@/lib/utils";
import { getMovie, getSimilarMovies } from "@/lib/api";
import { useInteractionStore } from "@/stores/interactionStore";
import { useAuthStore } from "@/stores/authStore";
import type { Movie, MovieDetail } from "@/types";
import MovieCard from "./MovieCard";

interface MovieModalProps {
  movie: Movie;
  onClose: () => void;
}

export default function MovieModal({ movie, onClose }: MovieModalProps) {
  const [detail, setDetail] = useState<MovieDetail | null>(null);
  const [similar, setSimilar] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [ratingHover, setRatingHover] = useState(0);

  const { isAuthenticated } = useAuthStore();
  const { interactions, fetchInteraction, toggleFavorite, setRating } = useInteractionStore();
  const interaction = interactions[movie.id];

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [movieDetail, similarMovies] = await Promise.all([
          getMovie(movie.id),
          getSimilarMovies(movie.id, 6),
        ]);
        setDetail(movieDetail);
        setSimilar(similarMovies);

        // 상호작용 상태 조회
        if (isAuthenticated) {
          await fetchInteraction(movie.id);
        }
      } catch (error) {
        console.error("Failed to fetch movie details:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = "unset";
    };
  }, [movie.id, isAuthenticated, fetchInteraction]);

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleFavoriteClick = async () => {
    if (!isAuthenticated) {
      alert("로그인이 필요합니다.");
      return;
    }
    try {
      await toggleFavorite(movie.id);
    } catch (error) {
      console.error("Failed to toggle favorite:", error);
      alert("찜하기에 실패했습니다.");
    }
  };

  const handleRatingClick = async (score: number) => {
    if (!isAuthenticated) {
      alert("로그인이 필요합니다.");
      return;
    }
    try {
      await setRating(movie.id, score);
    } catch (error) {
      console.error("Failed to set rating:", error);
      alert("평점 등록에 실패했습니다.");
    }
  };

  const isFavorited = interaction?.is_favorited ?? false;
  const userRating = interaction?.rating ?? 0;
  const displayRating = ratingHover || userRating;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80"
        onClick={handleBackdropClick}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="relative w-full max-w-4xl max-h-[90vh] bg-dark-100 rounded-lg overflow-hidden overflow-y-auto"
        >
          {/* Close Button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-10 w-10 h-10 bg-dark-200/80 hover:bg-dark-200 rounded-full flex items-center justify-center transition"
          >
            <X className="w-6 h-6 text-white" />
          </button>

          {/* Banner Image */}
          <div className="relative h-64 md:h-80">
            <Image
              src={getImageUrl(movie.poster_path, "w780")}
              alt={movie.title_ko || movie.title}
              fill
              className="object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-dark-100 to-transparent" />
          </div>

          {/* Content */}
          <div className="p-6 md:p-8 -mt-20 relative">
            {/* Title & Meta */}
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-2">
              {movie.title_ko || movie.title}
            </h2>

            <div className="flex flex-wrap items-center gap-3 text-sm text-white/70 mb-6">
              <div className="flex items-center space-x-1 text-yellow-400">
                <Star className="w-5 h-5 fill-current" />
                <span className="font-medium">{movie.vote_average.toFixed(1)}</span>
              </div>
              <span>|</span>
              <span>{formatDate(movie.release_date)}</span>
              {detail?.runtime && (
                <>
                  <span>|</span>
                  <span>{formatRuntime(detail.runtime)}</span>
                </>
              )}
              {movie.certification && (
                <>
                  <span>|</span>
                  <span className="px-2 py-0.5 border border-white/30 rounded text-xs">
                    {movie.certification}
                  </span>
                </>
              )}
            </div>

            {/* Genres */}
            <div className="flex flex-wrap gap-2 mb-6">
              {movie.genres.map((genre, index) => {
                const genreName = typeof genre === 'string' ? genre : (genre as any)?.name_ko || (genre as any)?.name;
                return (
                  <span
                    key={genreName || index}
                    className="px-3 py-1 bg-white/10 rounded-full text-sm text-white/80"
                  >
                    {genreName}
                  </span>
                );
              })}
            </div>

            {/* Overview */}
            {loading ? (
              <div className="animate-pulse space-y-2 mb-6">
                <div className="h-4 bg-white/10 rounded w-full" />
                <div className="h-4 bg-white/10 rounded w-5/6" />
                <div className="h-4 bg-white/10 rounded w-4/6" />
              </div>
            ) : (
              <p className="text-white/80 leading-relaxed mb-6">
                {detail?.overview || "줄거리 정보가 없습니다."}
              </p>
            )}

            {/* Cast */}
            {detail?.cast_members && detail.cast_members.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-white mb-2">출연</h3>
                <p className="text-white/70">
                  {detail.cast_members.map((p) => p.name).join(", ")}
                </p>
              </div>
            )}

            {/* Action Buttons - 찜하기 & 평점 */}
            <div className="flex flex-col sm:flex-row gap-4 mb-8 p-4 bg-white/5 rounded-lg">
              {/* 찜하기 버튼 */}
              <button
                onClick={handleFavoriteClick}
                className={`flex items-center justify-center space-x-2 px-6 py-3 rounded-md font-medium transition ${
                  isFavorited
                    ? "bg-red-500 hover:bg-red-600 text-white"
                    : "bg-white/10 hover:bg-white/20 text-white"
                }`}
              >
                <Heart
                  className={`w-5 h-5 ${isFavorited ? "fill-current" : ""}`}
                />
                <span>{isFavorited ? "찜 완료" : "찜하기"}</span>
              </button>

              {/* 별점 */}
              <div className="flex items-center space-x-3">
                <span className="text-white/70 text-sm">내 평점:</span>
                <div className="flex items-center space-x-1">
                  {[1, 2, 3, 4, 5].map((score) => (
                    <button
                      key={score}
                      onClick={() => handleRatingClick(score)}
                      onMouseEnter={() => setRatingHover(score)}
                      onMouseLeave={() => setRatingHover(0)}
                      className="p-1 transition-transform hover:scale-110"
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
                  <span className="text-yellow-400 font-medium ml-2">
                    {userRating.toFixed(1)}
                  </span>
                )}
              </div>
            </div>

            {/* Similar Movies */}
            {similar.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">비슷한 영화</h3>
                <div className="flex space-x-3 overflow-x-auto hide-scrollbar pb-4">
                  {similar.map((m, i) => (
                    <MovieCard key={m.id} movie={m} index={i} />
                  ))}
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
