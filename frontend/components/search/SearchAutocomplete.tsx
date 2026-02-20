"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Film, User, X, Star, Sparkles } from "lucide-react";
import { useDebounce } from "@/hooks/useDebounce";
import {
  searchAutocomplete,
  semanticSearch,
  type AutocompleteResult,
  type SemanticSearchResult,
} from "@/lib/api";
import { trackEvent } from "@/lib/eventTracker";
import { getImageUrl } from "@/lib/utils";
import { isNaturalLanguageQuery } from "@/lib/searchUtils";
import HighlightText from "@/components/ui/HighlightText";

interface SearchAutocompleteProps {
  onMovieSelect?: (movieId: number) => void;
  placeholder?: string;
  className?: string;
  inputClassName?: string;
  compact?: boolean;
  onClose?: () => void;
}

export default function SearchAutocomplete({
  onMovieSelect,
  placeholder = "영화, 배우, 감독을 검색하세요...",
  className = "",
  inputClassName = "",
  compact = false,
  onClose,
}: SearchAutocompleteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<AutocompleteResult | null>(null);
  const [semanticResults, setSemanticResults] = useState<SemanticSearchResult[]>([]);
  const [isSemanticLoading, setIsSemanticLoading] = useState(false);
  const [isSemanticMode, setIsSemanticMode] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const debouncedQuery = useDebounce(query, 300);

  // Build flat list of selectable items for keyboard navigation
  const flatItems = useMemo(() => {
    const items: Array<
      | { type: "semantic"; id: number }
      | { type: "movie"; id: number }
      | { type: "person"; name: string }
      | { type: "search" }
    > = [];

    // Semantic results first
    semanticResults.forEach((m) => items.push({ type: "semantic", id: m.id }));

    // Then keyword results
    if (results) {
      results.movies.forEach((m) => items.push({ type: "movie", id: m.id }));
      results.people.forEach((p) => items.push({ type: "person", name: p.name }));
    }

    if (
      semanticResults.length > 0 ||
      (results && (results.movies.length > 0 || results.people.length > 0))
    ) {
      items.push({ type: "search" });
    }
    return items;
  }, [results, semanticResults]);

  // Fetch autocomplete results
  useEffect(() => {
    const fetchResults = async () => {
      if (debouncedQuery.length < 1) {
        setResults(null);
        setSemanticResults([]);
        setIsSemanticMode(false);
        return;
      }

      setIsLoading(true);

      // Check if natural language query
      const isNL = isNaturalLanguageQuery(debouncedQuery);
      setIsSemanticMode(isNL);

      try {
        // Always run keyword search
        const data = await searchAutocomplete(debouncedQuery);
        setResults(data);
        setActiveIndex(-1);
        trackEvent({
          event_type: "search",
          metadata: {
            query: debouncedQuery,
            result_count: data.movies.length + data.people.length,
            is_semantic: isNL,
          },
        });
      } catch (error) {
        console.error("Autocomplete error:", error);
        setResults(null);
      } finally {
        setIsLoading(false);
      }

      // Run semantic search in parallel if NL query
      if (isNL) {
        setIsSemanticLoading(true);
        try {
          const semData = await semanticSearch(debouncedQuery, 8);
          if (!semData.fallback) {
            setSemanticResults(semData.results);
          } else {
            setSemanticResults([]);
          }
        } catch {
          setSemanticResults([]);
        } finally {
          setIsSemanticLoading(false);
        }
      } else {
        setSemanticResults([]);
      }
    };

    fetchResults();
  }, [debouncedQuery]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleMovieClick = useCallback(
    (movieId: number) => {
      setIsOpen(false);
      setQuery("");
      if (onMovieSelect) {
        onMovieSelect(movieId);
      } else {
        router.push(`/movies/${movieId}`);
      }
    },
    [onMovieSelect, router]
  );

  const handlePersonClick = useCallback(
    (personName: string) => {
      setIsOpen(false);
      setQuery("");
      router.push(`/movies?query=${encodeURIComponent(personName)}`);
    },
    [router]
  );

  const handleFullSearch = useCallback(() => {
    if (query.trim()) {
      setIsOpen(false);
      router.push(`/movies?query=${encodeURIComponent(query.trim())}`);
      onClose?.();
    }
  }, [query, router, onClose]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleFullSearch();
  };

  const handleClear = () => {
    setQuery("");
    setResults(null);
    setSemanticResults([]);
    setActiveIndex(-1);
    inputRef.current?.focus();
  };

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!isOpen || flatItems.length === 0) {
        if (e.key === "Escape") {
          setIsOpen(false);
          onClose?.();
        }
        return;
      }

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setActiveIndex((prev) => (prev < flatItems.length - 1 ? prev + 1 : 0));
          break;
        case "ArrowUp":
          e.preventDefault();
          setActiveIndex((prev) => (prev > 0 ? prev - 1 : flatItems.length - 1));
          break;
        case "Enter":
          e.preventDefault();
          if (activeIndex >= 0 && activeIndex < flatItems.length) {
            const item = flatItems[activeIndex];
            if (item.type === "semantic" || item.type === "movie") handleMovieClick(item.id);
            else if (item.type === "person") handlePersonClick(item.name);
            else handleFullSearch();
          } else {
            handleFullSearch();
          }
          break;
        case "Escape":
          setIsOpen(false);
          setActiveIndex(-1);
          onClose?.();
          break;
      }
    },
    [isOpen, flatItems, activeIndex, handleMovieClick, handlePersonClick, handleFullSearch, onClose]
  );

  // Scroll active item into view
  useEffect(() => {
    if (activeIndex < 0 || !listRef.current) return;
    const items = listRef.current.querySelectorAll("[data-autocomplete-item]");
    items[activeIndex]?.scrollIntoView({ block: "nearest" });
  }, [activeIndex]);

  const showDropdown =
    isOpen &&
    query.length > 0 &&
    (results || isLoading || isSemanticLoading || semanticResults.length > 0);

  // Track item index for keyboard nav
  let itemIndex = -1;

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <Search
            className={`absolute left-${compact ? "3" : "4"} top-1/2 -translate-y-1/2 ${compact ? "w-4 h-4" : "w-5 h-5"} text-white/40`}
          />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setIsOpen(true);
              setActiveIndex(-1);
            }}
            onFocus={() => setIsOpen(true)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className={
              inputClassName ||
              `w-full ${compact ? "pl-10 pr-8 py-1.5 text-sm" : "pl-12 pr-10 py-3"} bg-dark-100 border border-white/10 rounded-lg text-white placeholder-white/40 focus:outline-none focus:border-primary-500 transition`
            }
            autoComplete="off"
          />
          {query && (
            <button
              type="button"
              onClick={handleClear}
              className={`absolute right-${compact ? "3" : "4"} top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70 transition`}
            >
              <X className={compact ? "w-4 h-4" : "w-5 h-5"} />
            </button>
          )}
        </div>
      </form>

      {/* Dropdown */}
      <AnimatePresence>
        {showDropdown && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
            className="absolute z-50 w-full mt-2 bg-dark-100 border border-white/10 rounded-lg shadow-2xl overflow-hidden"
          >
            {isLoading && !results ? (
              <div className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                  <span className="text-white/60 text-sm">검색 중...</span>
                </div>
              </div>
            ) : (
              <div ref={listRef} className="max-h-96 overflow-y-auto">
                {/* Semantic AI Results */}
                {isSemanticMode && (isSemanticLoading || semanticResults.length > 0) && (
                  <div>
                    <div className="px-4 py-2 bg-gradient-to-r from-purple-900/30 to-dark-200/50 flex items-center space-x-2">
                      <Sparkles className="w-4 h-4 text-purple-400" />
                      <span className="text-xs font-medium text-purple-300 uppercase tracking-wide">
                        AI 추천 결과
                      </span>
                    </div>
                    {isSemanticLoading ? (
                      <div className="px-4 py-3 flex items-center space-x-3">
                        <div className="w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
                        <span className="text-white/50 text-sm">AI 추천 검색 중...</span>
                      </div>
                    ) : (
                      semanticResults.map((movie) => {
                        itemIndex++;
                        const isActive = itemIndex === activeIndex;
                        const year = movie.release_date?.split("-")[0];
                        return (
                          <button
                            key={`sem-${movie.id}`}
                            data-autocomplete-item
                            onClick={() => handleMovieClick(movie.id)}
                            onMouseEnter={() => setActiveIndex(itemIndex)}
                            className={`w-full flex items-center space-x-3 px-4 py-3 transition text-left ${
                              isActive ? "bg-white/10" : "hover:bg-white/5"
                            }`}
                          >
                            <div className="relative w-10 h-14 flex-shrink-0 bg-dark-200 rounded overflow-hidden">
                              {movie.poster_path ? (
                                <Image
                                  src={getImageUrl(movie.poster_path, "w92")}
                                  alt={movie.title_ko || movie.title}
                                  fill
                                  className="object-cover"
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center">
                                  <Film className="w-5 h-5 text-white/20" />
                                </div>
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-white font-medium truncate">
                                {movie.title_ko || movie.title}
                              </p>
                              <div className="flex items-center gap-2 text-white/50 text-sm">
                                <span>{year || "연도 미상"}</span>
                                {movie.weighted_score != null && (
                                  <span className="flex items-center gap-0.5">
                                    <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                                    {movie.weighted_score}
                                  </span>
                                )}
                                {movie.genres.length > 0 && (
                                  <span className="text-white/30 truncate">
                                    {movie.genres.slice(0, 2).join(", ")}
                                  </span>
                                )}
                              </div>
                            </div>
                          </button>
                        );
                      })
                    )}
                  </div>
                )}

                {/* Keyword Movies */}
                {results && results.movies.length > 0 && (
                  <div>
                    <div className="px-4 py-2 bg-dark-200/50 flex items-center space-x-2">
                      <Film className="w-4 h-4 text-primary-500" />
                      <span className="text-xs font-medium text-white/60 uppercase tracking-wide">
                        {isSemanticMode ? "검색 결과" : "영화"}
                      </span>
                    </div>
                    {results.movies.map((movie, movieIdx) => {
                      itemIndex++;
                      const isActive = itemIndex === activeIndex;
                      return (
                        <button
                          key={movie.id}
                          data-autocomplete-item
                          onClick={() => {
                            trackEvent({
                              event_type: "search_click",
                              movie_id: movie.id,
                              metadata: { query, position: movieIdx },
                            });
                            handleMovieClick(movie.id);
                          }}
                          onMouseEnter={() => setActiveIndex(itemIndex)}
                          className={`w-full flex items-center space-x-3 px-4 py-3 transition text-left ${
                            isActive ? "bg-white/10" : "hover:bg-white/5"
                          }`}
                        >
                          <div className="relative w-10 h-14 flex-shrink-0 bg-dark-200 rounded overflow-hidden">
                            {movie.poster_path ? (
                              <Image
                                src={getImageUrl(movie.poster_path, "w92")}
                                alt={movie.title}
                                fill
                                className="object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center">
                                <Film className="w-5 h-5 text-white/20" />
                              </div>
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-white font-medium truncate">
                              <HighlightText text={movie.title} query={query} />
                            </p>
                            <div className="flex items-center gap-2 text-white/50 text-sm">
                              <span>{movie.year || "연도 미상"}</span>
                              {movie.weighted_score && (
                                <span className="flex items-center gap-0.5">
                                  <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                                  {movie.weighted_score}
                                </span>
                              )}
                              {movie.title !== movie.title_en && (
                                <span className="text-white/30 truncate">
                                  <HighlightText
                                    text={movie.title_en}
                                    query={query}
                                    highlightClassName="font-bold text-white/60"
                                  />
                                </span>
                              )}
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* People */}
                {results && results.people.length > 0 && (
                  <div>
                    <div className="px-4 py-2 bg-dark-200/50 flex items-center space-x-2">
                      <User className="w-4 h-4 text-primary-500" />
                      <span className="text-xs font-medium text-white/60 uppercase tracking-wide">
                        배우/감독
                      </span>
                    </div>
                    {results.people.map((person) => {
                      itemIndex++;
                      const isActive = itemIndex === activeIndex;
                      return (
                        <button
                          key={person.id}
                          data-autocomplete-item
                          onClick={() => handlePersonClick(person.name)}
                          onMouseEnter={() => setActiveIndex(itemIndex)}
                          className={`w-full flex items-center space-x-3 px-4 py-3 transition text-left ${
                            isActive ? "bg-white/10" : "hover:bg-white/5"
                          }`}
                        >
                          <div className="w-10 h-10 flex-shrink-0 bg-dark-200 rounded-full flex items-center justify-center">
                            <User className="w-5 h-5 text-white/30" />
                          </div>
                          <p className="text-white">
                            <HighlightText text={person.name} query={query} />
                          </p>
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* No results */}
                {results &&
                  results.movies.length === 0 &&
                  results.people.length === 0 &&
                  semanticResults.length === 0 &&
                  !isSemanticLoading && (
                    <div className="p-6 text-center">
                      <Search className="w-8 h-8 text-white/20 mx-auto mb-2" />
                      <p className="text-white/60">검색 결과가 없습니다</p>
                      <p className="text-white/40 text-sm mt-1">다른 키워드로 검색해보세요</p>
                    </div>
                  )}

                {/* Search all */}
                {((results && (results.movies.length > 0 || results.people.length > 0)) ||
                  semanticResults.length > 0) &&
                  (() => {
                    itemIndex++;
                    const isActive = itemIndex === activeIndex;
                    return (
                      <button
                        data-autocomplete-item
                        onClick={handleFullSearch}
                        onMouseEnter={() => setActiveIndex(itemIndex)}
                        className={`w-full px-4 py-3 text-primary-400 text-sm font-medium transition ${
                          isActive ? "bg-primary-600/30" : "bg-primary-600/20 hover:bg-primary-600/30"
                        }`}
                      >
                        &quot;{query}&quot; 전체 검색 결과 보기
                      </button>
                    );
                  })()}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
