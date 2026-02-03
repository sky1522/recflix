"use client";

import { Suspense, useState, useEffect, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Film, RefreshCw } from "lucide-react";
import { getMovies, getGenres, getPopularMovies } from "@/lib/api";
import type { Movie, Genre } from "@/types";
import MovieCard from "@/components/movie/MovieCard";
import MovieModal from "@/components/movie/MovieModal";
import SearchAutocomplete from "@/components/search/SearchAutocomplete";
import { MovieGridSkeleton } from "@/components/ui/Skeleton";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";

const SORT_OPTIONS = [
  { value: "popularity", label: "인기순" },
  { value: "vote_average", label: "평점순" },
  { value: "release_date", label: "최신순" },
];

function MoviesPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [movies, setMovies] = useState<Movie[]>([]);
  const [genres, setGenres] = useState<Genre[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [totalPages, setTotalPages] = useState(1);
  const [recommendedMovies, setRecommendedMovies] = useState<Movie[]>([]);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);

  // URL params
  const query = searchParams.get("query") || "";
  const selectedGenre = searchParams.get("genre") || "";
  const sortBy = searchParams.get("sort") || "popularity";
  const [currentPage, setCurrentPage] = useState(1);

  // Infinite scroll mode
  const [useInfiniteMode, setUseInfiniteMode] = useState(false);

  const hasMore = currentPage < totalPages;

  const updateParams = useCallback(
    (updates: Record<string, string | number | null>) => {
      const params = new URLSearchParams(searchParams.toString());

      Object.entries(updates).forEach(([key, value]) => {
        if (value === null || value === "") {
          params.delete(key);
        } else {
          params.set(key, value.toString());
        }
      });

      router.push(`/movies?${params.toString()}`);
    },
    [searchParams, router]
  );

  // Fetch genres
  useEffect(() => {
    const fetchGenres = async () => {
      try {
        const data = await getGenres();
        setGenres(data);
      } catch (error) {
        console.error("Failed to fetch genres:", error);
      }
    };
    fetchGenres();
  }, []);

  // Fetch movies
  useEffect(() => {
    const fetchMovies = async () => {
      setLoading(true);
      setCurrentPage(1);
      try {
        const data = await getMovies({
          query: query || undefined,
          genres: selectedGenre || undefined,
          page: 1,
          page_size: 24,
          sort_by: sortBy,
        });
        setMovies(data.items);
        setTotalPages(data.total_pages);

        // Fetch recommendations if no results
        if (data.items.length === 0 && query) {
          const popular = await getPopularMovies(12);
          setRecommendedMovies(popular);
        } else {
          setRecommendedMovies([]);
        }
      } catch (error) {
        console.error("Failed to fetch movies:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchMovies();
  }, [query, selectedGenre, sortBy]);

  // Load more function for infinite scroll
  const loadMore = useCallback(async () => {
    if (loadingMore || !hasMore) return;

    setLoadingMore(true);
    try {
      const nextPage = currentPage + 1;
      const data = await getMovies({
        query: query || undefined,
        genres: selectedGenre || undefined,
        page: nextPage,
        page_size: 24,
        sort_by: sortBy,
      });
      setMovies((prev) => [...prev, ...data.items]);
      setCurrentPage(nextPage);
    } catch (error) {
      console.error("Failed to load more movies:", error);
    } finally {
      setLoadingMore(false);
    }
  }, [currentPage, hasMore, loadingMore, query, selectedGenre, sortBy]);

  const { loadMoreRef } = useInfiniteScroll({
    onLoadMore: loadMore,
    hasMore,
    isLoading: loadingMore,
  });

  const handleMovieSelect = (movieId: number) => {
    const movie = movies.find((m) => m.id === movieId);
    if (movie) {
      setSelectedMovie(movie);
    }
  };

  return (
    <div className="min-h-screen bg-dark-200 pt-20 pb-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Search & Filters */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-6">영화 검색</h1>

          {/* Search Autocomplete */}
          <div className="mb-6">
            <SearchAutocomplete
              onMovieSelect={handleMovieSelect}
              placeholder="영화 제목, 배우, 감독을 검색하세요..."
            />
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            {/* Genre Filter */}
            <select
              value={selectedGenre}
              onChange={(e) => updateParams({ genre: e.target.value })}
              className="px-4 py-2.5 bg-dark-100 border border-white/10 rounded-lg text-white focus:outline-none focus:border-primary-500 transition"
            >
              <option value="">모든 장르</option>
              {genres.map((genre) => (
                <option key={genre.id} value={genre.name_ko || genre.name}>
                  {genre.name_ko || genre.name}
                </option>
              ))}
            </select>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => updateParams({ sort: e.target.value })}
              className="px-4 py-2.5 bg-dark-100 border border-white/10 rounded-lg text-white focus:outline-none focus:border-primary-500 transition"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            {/* Infinite scroll toggle */}
            <button
              onClick={() => setUseInfiniteMode(!useInfiniteMode)}
              className={`px-4 py-2.5 rounded-lg transition flex items-center space-x-2 ${
                useInfiniteMode
                  ? "bg-primary-600 text-white"
                  : "bg-white/10 text-white/70 hover:bg-white/20"
              }`}
            >
              <RefreshCw className="w-4 h-4" />
              <span>무한 스크롤</span>
            </button>

            {/* Clear Filters */}
            {(query || selectedGenre) && (
              <button
                onClick={() => router.push("/movies")}
                className="px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white rounded-lg transition"
              >
                필터 초기화
              </button>
            )}
          </div>

          {/* Active search query indicator */}
          {query && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 flex items-center space-x-2"
            >
              <span className="text-white/60">검색어:</span>
              <span className="px-3 py-1 bg-primary-600/20 text-primary-400 rounded-full text-sm">
                &quot;{query}&quot;
              </span>
            </motion.div>
          )}
        </div>

        {/* Results */}
        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="skeleton"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <MovieGridSkeleton count={24} />
            </motion.div>
          ) : movies.length === 0 ? (
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
                검색 결과가 없습니다
              </h3>
              <p className="text-white/60 mb-8">
                {query
                  ? `"${query}"에 대한 검색 결과를 찾을 수 없습니다.`
                  : "조건에 맞는 영화가 없습니다."}
              </p>

              {/* Recommended movies when no results */}
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
            </motion.div>
          ) : (
            <motion.div
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {movies.map((movie, index) => (
                  <MovieCard key={movie.id} movie={movie} index={index} />
                ))}
              </div>

              {/* Infinite scroll mode */}
              {useInfiniteMode ? (
                <>
                  {/* Loading more indicator */}
                  {loadingMore && (
                    <div className="flex justify-center items-center py-8">
                      <div className="w-8 h-8 border-3 border-primary-500 border-t-transparent rounded-full animate-spin" />
                    </div>
                  )}

                  {/* Intersection observer target */}
                  {hasMore && <div ref={loadMoreRef} className="h-10" />}

                  {/* End of results */}
                  {!hasMore && movies.length > 0 && (
                    <p className="text-center text-white/40 py-8">
                      모든 영화를 불러왔습니다
                    </p>
                  )}
                </>
              ) : (
                /* Pagination */
                totalPages > 1 && (
                  <div className="flex justify-center items-center space-x-2 mt-12">
                    <button
                      onClick={() => {
                        setCurrentPage(Math.max(1, currentPage - 1));
                        // Refetch with new page
                        const fetchPage = async () => {
                          setLoading(true);
                          const data = await getMovies({
                            query: query || undefined,
                            genres: selectedGenre || undefined,
                            page: Math.max(1, currentPage - 1),
                            page_size: 24,
                            sort_by: sortBy,
                          });
                          setMovies(data.items);
                          setLoading(false);
                        };
                        fetchPage();
                      }}
                      disabled={currentPage === 1}
                      className="px-4 py-2 bg-dark-100 hover:bg-dark-100/70 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition"
                    >
                      이전
                    </button>

                    <div className="flex items-center space-x-1">
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        let pageNum;
                        if (totalPages <= 5) {
                          pageNum = i + 1;
                        } else if (currentPage <= 3) {
                          pageNum = i + 1;
                        } else if (currentPage >= totalPages - 2) {
                          pageNum = totalPages - 4 + i;
                        } else {
                          pageNum = currentPage - 2 + i;
                        }
                        return (
                          <button
                            key={pageNum}
                            onClick={() => {
                              setCurrentPage(pageNum);
                              const fetchPage = async () => {
                                setLoading(true);
                                const data = await getMovies({
                                  query: query || undefined,
                                  genres: selectedGenre || undefined,
                                  page: pageNum,
                                  page_size: 24,
                                  sort_by: sortBy,
                                });
                                setMovies(data.items);
                                setLoading(false);
                              };
                              fetchPage();
                            }}
                            className={`w-10 h-10 rounded-lg transition ${
                              currentPage === pageNum
                                ? "bg-primary-600 text-white"
                                : "bg-dark-100 text-white/70 hover:bg-dark-100/70"
                            }`}
                          >
                            {pageNum}
                          </button>
                        );
                      })}
                    </div>

                    <button
                      onClick={() => {
                        setCurrentPage(Math.min(totalPages, currentPage + 1));
                        const fetchPage = async () => {
                          setLoading(true);
                          const data = await getMovies({
                            query: query || undefined,
                            genres: selectedGenre || undefined,
                            page: Math.min(totalPages, currentPage + 1),
                            page_size: 24,
                            sort_by: sortBy,
                          });
                          setMovies(data.items);
                          setLoading(false);
                        };
                        fetchPage();
                      }}
                      disabled={currentPage === totalPages}
                      className="px-4 py-2 bg-dark-100 hover:bg-dark-100/70 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition"
                    >
                      다음
                    </button>
                  </div>
                )
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Movie Modal */}
      {selectedMovie && (
        <MovieModal movie={selectedMovie} onClose={() => setSelectedMovie(null)} />
      )}
    </div>
  );
}

// Loading fallback for Suspense
function MoviesPageLoading() {
  return (
    <div className="min-h-screen bg-dark-200 pt-20 pb-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="h-10 w-48 bg-dark-100 rounded animate-pulse mb-6" />
          <div className="h-12 w-full bg-dark-100 rounded-lg animate-pulse mb-6" />
          <div className="flex gap-4">
            <div className="h-10 w-32 bg-dark-100 rounded-lg animate-pulse" />
            <div className="h-10 w-32 bg-dark-100 rounded-lg animate-pulse" />
          </div>
        </div>
        <MovieGridSkeleton count={24} />
      </div>
    </div>
  );
}

export default function MoviesPage() {
  return (
    <Suspense fallback={<MoviesPageLoading />}>
      <MoviesPageContent />
    </Suspense>
  );
}
