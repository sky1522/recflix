"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Film, Sparkles } from "lucide-react";
import type { Movie } from "@/types";
import type { SemanticSearchResult } from "@/lib/api";
import MovieCard from "@/components/movie/MovieCard";
import { MovieGridSkeleton } from "@/components/ui/Skeleton";

interface MovieGridProps {
  movies: Movie[];
  loading: boolean;
  query: string;
  recommendedMovies: Movie[];
  /** Semantic search */
  semanticMovies: SemanticSearchResult[];
  isSemanticSearch: boolean;
  semanticLoading: boolean;
  semanticSearchTime: number;
  /** Infinite scroll */
  useInfiniteMode: boolean;
  loadingMore: boolean;
  hasMore: boolean;
  infinitePage: number;
  totalPages: number;
  loadMoreRef: (node: HTMLDivElement | null) => void;
  onLoadMore: () => void;
  /** Pagination */
  currentPage: number;
  onUpdateParams: (updates: Record<string, string | number | null>) => void;
}

function SemanticSection({
  movies: semanticMovies,
  loading,
  searchTime,
  query,
  hasKeywordResults,
}: {
  movies: SemanticSearchResult[];
  loading: boolean;
  searchTime: number;
  query: string;
  hasKeywordResults: boolean;
}) {
  return (
    <div className="mb-10">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-3 mb-6"
      >
        <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-900/40 to-purple-800/20 rounded-lg border border-purple-500/20">
          <Sparkles className="w-5 h-5 text-purple-400" />
          <span className="text-purple-300 font-medium">AI가 찾은 영화</span>
        </div>
        <span className="text-white/40 text-sm">
          &quot;{query}&quot;
          {searchTime > 0 && ` (${(searchTime / 1000).toFixed(2)}초)`}
        </span>
      </motion.div>

      {loading ? (
        <MovieGridSkeleton count={8} />
      ) : semanticMovies.length > 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4"
        >
          {semanticMovies.map((movie, index) => (
            <MovieCard
              key={`sem-${movie.id}`}
              movie={{
                id: movie.id,
                title: movie.title,
                title_ko: movie.title_ko,
                poster_path: movie.poster_path,
                release_date: movie.release_date,
                genres: movie.genres,
                vote_average: movie.weighted_score ?? 0,
                vote_count: 0,
                popularity: 0,
                certification: null,
                runtime: null,
                is_adult: false,
              }}
              index={index}
            />
          ))}
        </motion.div>
      ) : null}

      {hasKeywordResults && semanticMovies.length > 0 && (
        <div className="mt-8 border-t border-white/10 pt-6">
          <h3 className="text-lg font-semibold text-white/70">키워드 검색 결과</h3>
        </div>
      )}
    </div>
  );
}

function Pagination({
  currentPage,
  totalPages,
  onUpdateParams,
}: {
  currentPage: number;
  totalPages: number;
  onUpdateParams: (updates: Record<string, string | number | null>) => void;
}) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex justify-center items-center space-x-2 mt-12">
      <button
        onClick={() => onUpdateParams({ page: Math.max(1, currentPage - 1) })}
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
              onClick={() => onUpdateParams({ page: pageNum })}
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
        onClick={() => onUpdateParams({ page: Math.min(totalPages, currentPage + 1) })}
        disabled={currentPage === totalPages}
        className="px-4 py-2 bg-dark-100 hover:bg-dark-100/70 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition"
      >
        다음
      </button>
    </div>
  );
}

export default function MovieGrid({
  movies,
  loading,
  query,
  recommendedMovies,
  semanticMovies,
  isSemanticSearch,
  semanticLoading,
  semanticSearchTime,
  useInfiniteMode,
  loadingMore,
  hasMore,
  infinitePage,
  totalPages,
  loadMoreRef,
  onLoadMore,
  currentPage,
  onUpdateParams,
}: MovieGridProps) {
  return (
    <>
      {/* Semantic Search Results */}
      {isSemanticSearch && (
        <SemanticSection
          movies={semanticMovies}
          loading={semanticLoading}
          searchTime={semanticSearchTime}
          query={query}
          hasKeywordResults={movies.length > 0}
        />
      )}

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
                <MovieCard key={movie.id} movie={movie} index={index} highlightQuery={query} />
              ))}
            </div>

            {/* Infinite scroll mode */}
            {useInfiniteMode ? (
              <>
                {loadingMore && (
                  <div className="flex justify-center items-center py-8">
                    <div className="w-8 h-8 border-3 border-primary-500 border-t-transparent rounded-full animate-spin" />
                  </div>
                )}
                <div ref={loadMoreRef} className="h-10" />
                {hasMore && !loadingMore && (
                  <div className="flex justify-center py-6">
                    <button
                      onClick={onLoadMore}
                      className="px-6 py-3 bg-white/10 hover:bg-white/20 text-white rounded-lg transition"
                    >
                      더 보기 ({infinitePage} / {totalPages} 페이지)
                    </button>
                  </div>
                )}
                {!hasMore && movies.length > 0 && (
                  <p className="text-center text-white/40 py-8">
                    모든 영화를 불러왔습니다
                  </p>
                )}
              </>
            ) : (
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onUpdateParams={onUpdateParams}
              />
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
