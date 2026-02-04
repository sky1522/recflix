"use client";

import { useRef, useState } from "react";
import MovieCard from "./MovieCard";
import type { Movie } from "@/types";

interface MovieRowProps {
  title: string;
  description?: string | null;
  movies: Movie[];
}

export default function MovieRow({ title, description, movies }: MovieRowProps) {
  const rowRef = useRef<HTMLDivElement>(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(true);

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
      <div className="mb-3 flex items-baseline gap-3">
        <h2 className="text-xl md:text-2xl font-bold text-white">{title}</h2>
        {description && (
          <p className="text-sm text-gray-400">{description}</p>
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
          {movies.map((movie, index) => (
            <MovieCard key={movie.id} movie={movie} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
}
