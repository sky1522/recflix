"use client";

import { Suspense, useState, useEffect, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { getMovies, getGenres, getPopularMovies, semanticSearch, type SemanticSearchResult } from "@/lib/api";
import { isNaturalLanguageQuery } from "@/lib/searchUtils";
import type { Movie, Genre } from "@/types";
import MovieModal from "@/components/movie/MovieModal";
import MovieFilters from "@/components/movie/MovieFilters";
import MovieGrid from "@/components/movie/MovieGrid";
import SearchAutocomplete from "@/components/search/SearchAutocomplete";
import { MovieGridSkeleton } from "@/components/ui/Skeleton";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";

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

  // Semantic search state
  const [semanticMovies, setSemanticMovies] = useState<SemanticSearchResult[]>([]);
  const [isSemanticSearch, setIsSemanticSearch] = useState(false);
  const [semanticLoading, setSemanticLoading] = useState(false);
  const [semanticSearchTime, setSemanticSearchTime] = useState(0);

  // URL params
  const query = searchParams.get("query") || "";
  const selectedGenre = searchParams.get("genre") || "";
  const selectedAgeRating = searchParams.get("age_rating") || "";
  const sortBy = searchParams.get("sort") || "popularity";
  const currentPage = Number(searchParams.get("page")) || 1;
  const selectedCountry = searchParams.get("country") || "";
  const selectedKeyword = searchParams.get("keyword") || "";
  const selectedMbti = searchParams.get("mbti") || "";
  const selectedWeather = searchParams.get("weather") || "";

  // Infinite scroll mode
  const [useInfiniteMode, setUseInfiniteMode] = useState(false);
  const [infinitePage, setInfinitePage] = useState(1);

  const hasMore = useInfiniteMode
    ? infinitePage < totalPages
    : currentPage < totalPages;

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

  // Fetch movies (reacts to URL params including page)
  useEffect(() => {
    const fetchMovies = async () => {
      setLoading(true);
      setInfinitePage(currentPage);
      try {
        const data = await getMovies({
          query: query || undefined,
          genres: selectedGenre || undefined,
          age_rating: selectedAgeRating || undefined,
          country: selectedCountry || undefined,
          keyword: selectedKeyword || undefined,
          mbti: selectedMbti || undefined,
          weather: selectedWeather || undefined,
          page: currentPage,
          page_size: 24,
          sort_by: sortBy,
        });
        setMovies(data.items);
        setTotalPages(data.total_pages);

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
    window.scrollTo(0, 0);
  }, [query, selectedGenre, selectedAgeRating, sortBy, currentPage, selectedCountry, selectedKeyword, selectedMbti, selectedWeather]);

  // Semantic search for natural language queries
  useEffect(() => {
    if (!query || !isNaturalLanguageQuery(query)) {
      setIsSemanticSearch(false);
      setSemanticMovies([]);
      return;
    }

    const fetchSemantic = async () => {
      setSemanticLoading(true);
      setIsSemanticSearch(true);
      try {
        const data = await semanticSearch(query, 20);
        if (!data.fallback) {
          setSemanticMovies(data.results);
          setSemanticSearchTime(data.search_time_ms);
        } else {
          setSemanticMovies([]);
          setIsSemanticSearch(false);
        }
      } catch {
        setSemanticMovies([]);
        setIsSemanticSearch(false);
      } finally {
        setSemanticLoading(false);
      }
    };
    fetchSemantic();
  }, [query]);

  // Load more function for infinite scroll
  const loadMore = useCallback(async () => {
    if (loadingMore || infinitePage >= totalPages) return;

    setLoadingMore(true);
    try {
      const nextPage = infinitePage + 1;
      const data = await getMovies({
        query: query || undefined,
        genres: selectedGenre || undefined,
        age_rating: selectedAgeRating || undefined,
        country: selectedCountry || undefined,
        keyword: selectedKeyword || undefined,
        mbti: selectedMbti || undefined,
        weather: selectedWeather || undefined,
        page: nextPage,
        page_size: 24,
        sort_by: sortBy,
      });
      setMovies((prev) => [...prev, ...data.items]);
      setInfinitePage(nextPage);
    } catch (error) {
      console.error("Failed to load more movies:", error);
    } finally {
      setLoadingMore(false);
    }
  }, [infinitePage, totalPages, loadingMore, query, selectedGenre, selectedAgeRating, sortBy, selectedCountry, selectedKeyword, selectedMbti, selectedWeather]);

  const { loadMoreRef } = useInfiniteScroll({
    onLoadMore: loadMore,
    hasMore,
    isLoading: loadingMore,
    enabled: useInfiniteMode,
  });

  const handleMovieSelect = (movieId: number) => {
    const movie = movies.find((m) => m.id === movieId);
    if (movie) setSelectedMovie(movie);
  };

  return (
    <div className="min-h-screen bg-dark-200 pt-20 pb-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Search & Filters */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-6">영화 검색</h1>

          <div className="mb-6">
            <SearchAutocomplete
              onMovieSelect={handleMovieSelect}
              placeholder="영화 제목, 배우, 감독을 검색하세요..."
            />
          </div>

          <MovieFilters
            genres={genres}
            selectedGenre={selectedGenre}
            selectedAgeRating={selectedAgeRating}
            sortBy={sortBy}
            query={query}
            useInfiniteMode={useInfiniteMode}
            onUpdateParams={updateParams}
            onToggleInfiniteMode={() => {
              if (!useInfiniteMode) setInfinitePage(currentPage);
              setUseInfiniteMode(!useInfiniteMode);
            }}
            onClearFilters={() => router.push("/movies")}
          />

          {(query || selectedCountry || selectedKeyword || selectedMbti || selectedWeather) && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 flex items-center flex-wrap gap-2"
            >
              {query && (
                <span className="px-3 py-1 bg-primary-600/20 text-primary-400 rounded-full text-sm flex items-center gap-1.5">
                  검색: &quot;{query}&quot;
                  <button onClick={() => updateParams({ query: null, page: null })} className="hover:text-white transition">✕</button>
                </span>
              )}
              {selectedCountry && (
                <span className="px-3 py-1 bg-emerald-600/20 text-emerald-400 rounded-full text-sm flex items-center gap-1.5">
                  🌍 {selectedCountry}
                  <button onClick={() => updateParams({ country: null, page: null })} className="hover:text-white transition">✕</button>
                </span>
              )}
              {selectedKeyword && (
                <span className="px-3 py-1 bg-violet-600/20 text-violet-400 rounded-full text-sm flex items-center gap-1.5">
                  🏷️ {selectedKeyword}
                  <button onClick={() => updateParams({ keyword: null, page: null })} className="hover:text-white transition">✕</button>
                </span>
              )}
              {selectedMbti && (
                <span className="px-3 py-1 bg-amber-600/20 text-amber-400 rounded-full text-sm flex items-center gap-1.5">
                  🧠 {selectedMbti} 추천순
                  <button onClick={() => updateParams({ mbti: null, page: null })} className="hover:text-white transition">✕</button>
                </span>
              )}
              {selectedWeather && (
                <span className="px-3 py-1 bg-sky-600/20 text-sky-400 rounded-full text-sm flex items-center gap-1.5">
                  {{ sunny: "☀️ 맑은 날", rainy: "🌧️ 비 오는 날", cloudy: "☁️ 흐린 날", snowy: "❄️ 눈 오는 날" }[selectedWeather]} 추천순
                  <button onClick={() => updateParams({ weather: null, page: null })} className="hover:text-white transition">✕</button>
                </span>
              )}
            </motion.div>
          )}
        </div>

        <MovieGrid
          movies={movies}
          loading={loading}
          query={query}
          recommendedMovies={recommendedMovies}
          semanticMovies={semanticMovies}
          isSemanticSearch={isSemanticSearch}
          semanticLoading={semanticLoading}
          semanticSearchTime={semanticSearchTime}
          useInfiniteMode={useInfiniteMode}
          loadingMore={loadingMore}
          hasMore={hasMore}
          infinitePage={infinitePage}
          totalPages={totalPages}
          loadMoreRef={loadMoreRef}
          onLoadMore={loadMore}
          currentPage={currentPage}
          onUpdateParams={updateParams}
        />
      </div>

      {selectedMovie && (
        <MovieModal movie={selectedMovie} onClose={() => setSelectedMovie(null)} />
      )}
    </div>
  );
}

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
