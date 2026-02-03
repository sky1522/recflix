"use client";

import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Film, User, X } from "lucide-react";
import { useDebounce } from "@/hooks/useDebounce";
import { searchAutocomplete, type AutocompleteResult } from "@/lib/api";
import { getImageUrl } from "@/lib/utils";

interface SearchAutocompleteProps {
  onMovieSelect?: (movieId: number) => void;
  placeholder?: string;
  className?: string;
}

export default function SearchAutocomplete({
  onMovieSelect,
  placeholder = "영화, 배우, 감독을 검색하세요...",
  className = "",
}: SearchAutocompleteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<AutocompleteResult | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const debouncedQuery = useDebounce(query, 300);

  // Fetch autocomplete results
  useEffect(() => {
    const fetchResults = async () => {
      if (debouncedQuery.length < 1) {
        setResults(null);
        return;
      }

      setIsLoading(true);
      try {
        const data = await searchAutocomplete(debouncedQuery);
        setResults(data);
      } catch (error) {
        console.error("Autocomplete error:", error);
        setResults(null);
      } finally {
        setIsLoading(false);
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

  const handleMovieClick = (movieId: number) => {
    setIsOpen(false);
    setQuery("");
    if (onMovieSelect) {
      onMovieSelect(movieId);
    }
  };

  const handlePersonClick = (personName: string) => {
    setIsOpen(false);
    setQuery("");
    router.push(`/movies?query=${encodeURIComponent(personName)}`);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      setIsOpen(false);
      router.push(`/movies?query=${encodeURIComponent(query.trim())}`);
    }
  };

  const handleClear = () => {
    setQuery("");
    setResults(null);
    inputRef.current?.focus();
  };

  const showDropdown = isOpen && query.length > 0 && (results || isLoading);

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setIsOpen(true);
            }}
            onFocus={() => setIsOpen(true)}
            placeholder={placeholder}
            className="w-full pl-12 pr-10 py-3 bg-dark-100 border border-white/10 rounded-lg text-white placeholder-white/40 focus:outline-none focus:border-primary-500 transition"
          />
          {query && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70 transition"
            >
              <X className="w-5 h-5" />
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
            {isLoading ? (
              <div className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                  <span className="text-white/60 text-sm">검색 중...</span>
                </div>
              </div>
            ) : results ? (
              <div className="max-h-96 overflow-y-auto">
                {/* Movies */}
                {results.movies.length > 0 && (
                  <div>
                    <div className="px-4 py-2 bg-dark-200/50 flex items-center space-x-2">
                      <Film className="w-4 h-4 text-primary-500" />
                      <span className="text-xs font-medium text-white/60 uppercase tracking-wide">
                        영화
                      </span>
                    </div>
                    {results.movies.map((movie) => (
                      <button
                        key={movie.id}
                        onClick={() => handleMovieClick(movie.id)}
                        className="w-full flex items-center space-x-3 px-4 py-3 hover:bg-white/5 transition text-left"
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
                          <p className="text-white font-medium truncate">{movie.title}</p>
                          <p className="text-white/50 text-sm">
                            {movie.year || "연도 미상"}
                            {movie.title !== movie.title_en && (
                              <span className="ml-2 text-white/30">{movie.title_en}</span>
                            )}
                          </p>
                        </div>
                      </button>
                    ))}
                  </div>
                )}

                {/* People */}
                {results.people.length > 0 && (
                  <div>
                    <div className="px-4 py-2 bg-dark-200/50 flex items-center space-x-2">
                      <User className="w-4 h-4 text-primary-500" />
                      <span className="text-xs font-medium text-white/60 uppercase tracking-wide">
                        배우/감독
                      </span>
                    </div>
                    {results.people.map((person) => (
                      <button
                        key={person.id}
                        onClick={() => handlePersonClick(person.name)}
                        className="w-full flex items-center space-x-3 px-4 py-3 hover:bg-white/5 transition text-left"
                      >
                        <div className="w-10 h-10 flex-shrink-0 bg-dark-200 rounded-full flex items-center justify-center">
                          <User className="w-5 h-5 text-white/30" />
                        </div>
                        <p className="text-white">{person.name}</p>
                      </button>
                    ))}
                  </div>
                )}

                {/* No results */}
                {results.movies.length === 0 && results.people.length === 0 && (
                  <div className="p-6 text-center">
                    <Search className="w-8 h-8 text-white/20 mx-auto mb-2" />
                    <p className="text-white/60">검색 결과가 없습니다</p>
                    <p className="text-white/40 text-sm mt-1">
                      다른 키워드로 검색해보세요
                    </p>
                  </div>
                )}

                {/* Search all */}
                {(results.movies.length > 0 || results.people.length > 0) && (
                  <button
                    onClick={handleSubmit}
                    className="w-full px-4 py-3 bg-primary-600/20 hover:bg-primary-600/30 text-primary-400 text-sm font-medium transition"
                  >
                    &quot;{query}&quot; 전체 검색 결과 보기
                  </button>
                )}
              </div>
            ) : null}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
