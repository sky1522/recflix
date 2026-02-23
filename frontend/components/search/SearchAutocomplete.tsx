"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Search, X } from "lucide-react";
import { useDebounce } from "@/hooks/useDebounce";
import {
  searchAutocomplete,
  semanticSearch,
  type AutocompleteResult,
  type SemanticSearchResult,
} from "@/lib/api";
import { trackEvent } from "@/lib/eventTracker";
import { isNaturalLanguageQuery } from "@/lib/searchUtils";
import SearchResults from "@/components/search/SearchResults";

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

    semanticResults.forEach((m) => items.push({ type: "semantic", id: m.id }));

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

  // Fetch autocomplete results (keyword + semantic in parallel, with abort)
  useEffect(() => {
    if (debouncedQuery.length < 1) {
      setResults(null);
      setSemanticResults([]);
      setIsSemanticMode(false);
      return;
    }

    const abortController = new AbortController();
    const { signal } = abortController;

    const isNL = isNaturalLanguageQuery(debouncedQuery);
    setIsSemanticMode(isNL);
    setIsLoading(true);
    if (isNL) setIsSemanticLoading(true);

    const keywordPromise = searchAutocomplete(debouncedQuery, 8, signal);
    const semanticPromise = isNL ? semanticSearch(debouncedQuery, 8, signal) : null;

    const promises: Promise<unknown>[] = [keywordPromise];
    if (semanticPromise) promises.push(semanticPromise);

    Promise.allSettled(promises).then((settled) => {
      if (signal.aborted) return;

      const kwResult = settled[0];
      if (kwResult.status === "fulfilled") {
        const data = kwResult.value as Awaited<ReturnType<typeof searchAutocomplete>>;
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
      } else {
        if (!(kwResult.reason instanceof DOMException && kwResult.reason.name === "AbortError")) {
          console.error("Autocomplete error:", kwResult.reason);
        }
        setResults(null);
      }
      setIsLoading(false);

      if (isNL && settled.length > 1) {
        const semResult = settled[1];
        if (semResult.status === "fulfilled") {
          const semData = semResult.value as Awaited<ReturnType<typeof semanticSearch>>;
          setSemanticResults(!semData.fallback ? semData.results : []);
        } else {
          setSemanticResults([]);
        }
        setIsSemanticLoading(false);
      } else if (!isNL) {
        setSemanticResults([]);
      }
    });

    return () => { abortController.abort(); };
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
                <SearchResults
                  query={query}
                  results={results}
                  semanticResults={semanticResults}
                  isSemanticMode={isSemanticMode}
                  isSemanticLoading={isSemanticLoading}
                  activeIndex={activeIndex}
                  onMovieClick={handleMovieClick}
                  onPersonClick={handlePersonClick}
                  onFullSearch={handleFullSearch}
                  onSetActiveIndex={setActiveIndex}
                />
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
