"use client";

import { useRef, useState, useMemo, useCallback } from "react";
import { RefreshCw } from "lucide-react";
import MovieCard from "./MovieCard";
import type { Movie } from "@/types";

interface MovieRowProps {
  title: string;
  description?: string | null;
  movies: Movie[];
  displayCount?: number;
}

// Fisher-Yates shuffle
function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

export default function MovieRow({ title, description, movies, displayCount = 20 }: MovieRowProps) {
  const rowRef = useRef<HTMLDivElement>(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(true);
  const [shuffleKey, setShuffleKey] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Memoize displayed movies based on shuffleKey
  const displayedMovies = useMemo(() => {
    const shuffled = shuffleArray(movies);
    return shuffled.slice(0, displayCount);
  }, [movies, displayCount, shuffleKey]);

  const handleRefresh = useCallback(() => {
    setIsRefreshing(true);
    // Scroll back to start
    if (rowRef.current) {
      rowRef.current.scrollTo({ left: 0, behavior: "smooth" });
    }
    // Trigger reshuffle
    setTimeout(() => {
      setShuffleKey((prev) => prev + 1);
      setIsRefreshing(false);
    }, 300);
  }, []);

  const scroll = (direction: "left" | "right") => {
    if (!rowRef.current) return;
    const scrollAmount = rowRef.current.clientWidth * 0.8;
    const newScrollLeft =
      direction === "left"
        ? rowRef.current.scrollLeft - scrollAmount
        : rowRef.current.scrollLeft + scrollAmount;

    rowRef.current.scrollTo({
      left: newScrollLeft,
      behavior: "smooth",
    });
  };

  const handleScroll = () => {
    if (!rowRef.current) return;
    const { scrollLeft, scrollWidth, clientWidth } = rowRef.current;
    setShowLeftArrow(scrollLeft > 0);
    setShowRightArrow(scrollLeft < scrollWidth - clientWidth - 10);
  };

  if (!movies || movies.length === 0) return null;

  return (
    <section className="relative group/row">
      {/* Header - 한 줄 배치 */}
      <div className="mb-3 flex items-center gap-3">
        <h2 className="text-xl md:text-2xl font-bold text-white">{title}</h2>
        {description && (
          <p className="text-sm text-gray-400">{description}</p>
        )}
        {/* Refresh Button */}
        {movies.length > displayCount && (
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="ml-auto p-1.5 rounded-full hover:bg-white/10 transition-colors group/refresh"
            title="다른 영화 보기"
          >
            <RefreshCw
              className={`w-4 h-4 text-gray-400 group-hover/refresh:text-white transition-colors ${
                isRefreshing ? "animate-spin" : ""
              }`}
            />
          </button>
        )}
      </div>

      {/* Movie List */}
      <div className="relative">
        {/* Left Arrow */}
        {showLeftArrow && (
          <button
            onClick={() => scroll("left")}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-black/70 hover:bg-black/90 text-white p-2 rounded-r-md opacity-0 group-hover/row:opacity-100 transition-opacity"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        )}

        {/* Right Arrow */}
        {showRightArrow && (
          <button
            onClick={() => scroll("right")}
            className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-black/70 hover:bg-black/90 text-white p-2 rounded-l-md opacity-0 group-hover/row:opacity-100 transition-opacity"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        )}

        {/* Scrollable Container */}
        <div
          ref={rowRef}
          onScroll={handleScroll}
          className="flex space-x-3 overflow-x-auto hide-scrollbar pb-4"
        >
          {displayedMovies.map((movie, index) => (
            <MovieCard key={movie.id} movie={movie} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
}
