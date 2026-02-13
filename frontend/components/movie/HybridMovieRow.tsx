"use client";

import { useRef, useState, useMemo, useCallback } from "react";
import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight, Sparkles, RefreshCw } from "lucide-react";
import HybridMovieCard from "./HybridMovieCard";
import type { HybridMovie } from "@/types";

interface HybridMovieRowProps {
  title: string;
  description?: string | null;
  subtitle?: string;
  movies: HybridMovie[];
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

export default function HybridMovieRow({
  title,
  description,
  subtitle,
  movies,
  displayCount = 20,
}: HybridMovieRowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(true);
  const [shuffleKey, setShuffleKey] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Memoize displayed movies based on shuffleKey
  // 초기 렌더링(shuffleKey=0)에서는 백엔드 순서 유지, 새로고침 시에만 셔플
  const displayedMovies = useMemo(() => {
    if (shuffleKey === 0) {
      return movies.slice(0, displayCount);
    }
    const shuffled = shuffleArray(movies);
    return shuffled.slice(0, displayCount);
  }, [movies, displayCount, shuffleKey]);

  const handleRefresh = useCallback(() => {
    setIsRefreshing(true);
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ left: 0, behavior: "smooth" });
    }
    setTimeout(() => {
      setShuffleKey((prev) => prev + 1);
      setIsRefreshing(false);
    }, 300);
  }, []);

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
    setShowLeftArrow(scrollLeft > 0);
    setShowRightArrow(scrollLeft < scrollWidth - clientWidth - 10);
  };

  const scroll = (direction: "left" | "right") => {
    if (!scrollRef.current) return;
    const scrollAmount = scrollRef.current.clientWidth * 0.8;
    scrollRef.current.scrollBy({
      left: direction === "left" ? -scrollAmount : scrollAmount,
      behavior: "smooth",
    });
  };

  if (movies.length === 0) return null;

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="relative group"
    >
      {/* Header with gradient background */}
      <div className="mb-4 p-4 rounded-lg bg-gradient-to-r from-primary-600/20 to-purple-600/20 border border-primary-500/30">
        <div className="flex items-center gap-3">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-primary-400" />
            <h2 className="text-xl md:text-2xl font-bold text-white">{title}</h2>
          </div>
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
        {subtitle && (
          <p className="text-sm text-white/50 mt-1 truncate">{subtitle}</p>
        )}
      </div>

      {/* Scroll Container */}
      <div className="relative">
        {/* Left Arrow */}
        {showLeftArrow && (
          <button
            onClick={() => scroll("left")}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-10 h-10 bg-black/70 hover:bg-black/90 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <ChevronLeft className="w-6 h-6 text-white" />
          </button>
        )}

        {/* Right Arrow */}
        {showRightArrow && (
          <button
            onClick={() => scroll("right")}
            className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-10 h-10 bg-black/70 hover:bg-black/90 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <ChevronRight className="w-6 h-6 text-white" />
          </button>
        )}

        {/* Movie Cards */}
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="flex space-x-3 overflow-x-auto hide-scrollbar pb-4"
        >
          {displayedMovies.map((movie, index) => (
            <HybridMovieCard key={movie.id} movie={movie} index={index} />
          ))}
        </div>
      </div>
    </motion.section>
  );
}
