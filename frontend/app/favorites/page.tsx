"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Heart, Film, Trash2, LogIn } from "lucide-react";
import { getFavorites, toggleFavorite, getPopularMovies } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import type { Movie } from "@/types";
import MovieCard from "@/components/movie/MovieCard";
import { MovieGridSkeleton } from "@/components/ui/Skeleton";
import Link from "next/link";

export default function FavoritesPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuthStore();

  const [favorites, setFavorites] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [removingId, setRemovingId] = useState<number | null>(null);
  const [recommendedMovies, setRecommendedMovies] = useState<Movie[]>([]);

  const PAGE_SIZE = 20;

  // Fetch favorites
  const fetchFavorites = useCallback(async (pageNum: number, append = false) => {
    if (!isAuthenticated) return;

    try {
      if (append) {
        setLoadingMore(true);
      } else {
        setLoading(true);
      }

      const data = await getFavorites(pageNum, PAGE_SIZE);

      if (append) {
        setFavorites(prev => [...prev, ...data]);
      } else {
        setFavorites(data);
      }

      setHasMore(data.length === PAGE_SIZE);

      // If no favorites, get recommendations
      if (data.length === 0 && pageNum === 1) {
        const popular = await getPopularMovies(12);
        setRecommendedMovies(popular);
      }
    } catch (error) {
      console.error("Failed to fetch favorites:", error);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      fetchFavorites(1);
    } else if (!authLoading && !isAuthenticated) {
      setLoading(false);
    }
  }, [authLoading, isAuthenticated, fetchFavorites]);

  const handleLoadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchFavorites(nextPage, true);
  };

  const handleRemoveFavorite = async (movieId: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    setRemovingId(movieId);

    try {
      await toggleFavorite(movieId);
      setFavorites(prev => prev.filter(m => m.id !== movieId));
    } catch (error) {
      console.error("Failed to remove favorite:", error);
    } finally {
      setRemovingId(null);
    }
  };

  // Not logged in state
  if (!authLoading && !isAuthenticated) {
    return (
      <div className="min-h-screen bg-dark-200 pt-20 pb-12 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-24 h-24 bg-primary-500/10 rounded-full flex items-center justify-center mb-6">
              <Heart className="w-12 h-12 text-primary-500" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-3">
              로그인이 필요합니다
            </h1>
            <p className="text-white/60 text-center mb-8 max-w-md">
              찜한 영화 목록을 보려면 로그인해주세요.<br />
              좋아하는 영화를 저장하고 나만의 컬렉션을 만들어보세요.
            </p>
            <Link
              href="/login"
              className="flex items-center space-x-2 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition"
            >
              <LogIn className="w-5 h-5" />
              <span>로그인하기</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-200 pt-20 pb-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-2">
            <Heart className="w-8 h-8 text-primary-500 fill-primary-500" />
            <h1 className="text-3xl font-bold text-white">찜한 영화</h1>
          </div>
          <p className="text-white/60">
            {loading ? "불러오는 중..." : `총 ${favorites.length}개의 영화`}
          </p>
        </div>

        {/* Content */}
        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="skeleton"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <MovieGridSkeleton count={12} />
            </motion.div>
          ) : favorites.length === 0 ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="text-center py-12"
            >
              <div className="inline-flex items-center justify-center w-20 h-20 bg-white/5 rounded-full mb-6">
                <Film className="w-10 h-10 text-white/20" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">
                찜한 영화가 없습니다
              </h3>
              <p className="text-white/60 mb-8">
                마음에 드는 영화를 찾아 하트를 눌러보세요!
              </p>

              {/* Recommended movies */}
              {recommendedMovies.length > 0 && (
                <div className="mt-8">
                  <h4 className="text-lg font-semibold text-white mb-4 text-left">
                    이런 영화는 어떠세요?
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    {recommendedMovies.map((movie, index) => (
                      <MovieCard key={movie.id} movie={movie} index={index} />
                    ))}
                  </div>
                </div>
              )}

              <Link
                href="/movies"
                className="inline-flex items-center space-x-2 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition mt-6"
              >
                <Film className="w-5 h-5" />
                <span>영화 둘러보기</span>
              </Link>
            </motion.div>
          ) : (
            <motion.div
              key="favorites"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {/* Favorites Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                <AnimatePresence>
                  {favorites.map((movie, index) => (
                    <motion.div
                      key={movie.id}
                      layout
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      transition={{ delay: index * 0.02 }}
                      className="relative group"
                    >
                      <MovieCard movie={movie} index={0} />

                      {/* Remove button */}
                      <button
                        onClick={(e) => handleRemoveFavorite(movie.id, e)}
                        disabled={removingId === movie.id}
                        className="absolute top-2 left-2 p-2 bg-black/70 hover:bg-red-600 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-200 z-10"
                        title="찜 해제"
                      >
                        {removingId === movie.id ? (
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4 text-white" />
                        )}
                      </button>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>

              {/* Load More */}
              {hasMore && (
                <div className="flex justify-center mt-8">
                  <button
                    onClick={handleLoadMore}
                    disabled={loadingMore}
                    className="px-8 py-3 bg-white/10 hover:bg-white/20 disabled:opacity-50 text-white rounded-lg transition flex items-center space-x-2"
                  >
                    {loadingMore ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>불러오는 중...</span>
                      </>
                    ) : (
                      <span>더 보기</span>
                    )}
                  </button>
                </div>
              )}

              {/* End of list */}
              {!hasMore && favorites.length >= PAGE_SIZE && (
                <p className="text-center text-white/40 py-8">
                  모든 찜한 영화를 불러왔습니다
                </p>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
