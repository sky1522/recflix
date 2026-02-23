"use client";

import { RefreshCw } from "lucide-react";
import type { Genre } from "@/types";

const SORT_OPTIONS = [
  { value: "popularity", label: "인기순" },
  { value: "weighted_score", label: "평점순" },
  { value: "release_date", label: "최신순" },
];

const AGE_RATING_OPTIONS = [
  { value: "", label: "모든 등급" },
  { value: "family", label: "가족 (ALL/G/PG/12)" },
  { value: "teen", label: "청소년 (15세 이하)" },
  { value: "adult", label: "성인 포함" },
];

interface MovieFiltersProps {
  genres: Genre[];
  selectedGenre: string;
  selectedAgeRating: string;
  sortBy: string;
  query: string;
  useInfiniteMode: boolean;
  onUpdateParams: (updates: Record<string, string | number | null>) => void;
  onToggleInfiniteMode: () => void;
  onClearFilters: () => void;
}

export default function MovieFilters({
  genres,
  selectedGenre,
  selectedAgeRating,
  sortBy,
  query,
  useInfiniteMode,
  onUpdateParams,
  onToggleInfiniteMode,
  onClearFilters,
}: MovieFiltersProps) {
  return (
    <div className="flex flex-wrap gap-4">
      {/* Genre Filter */}
      <select
        value={selectedGenre}
        onChange={(e) => onUpdateParams({ genre: e.target.value, page: null })}
        aria-label="장르 선택"
        className="px-4 py-2.5 bg-dark-100 border border-white/10 rounded-lg text-white focus:outline-none focus:border-primary-500 transition"
      >
        <option value="">모든 장르</option>
        {genres.map((genre) => (
          <option key={genre.id} value={genre.name_ko || genre.name}>
            {genre.name_ko || genre.name}
          </option>
        ))}
      </select>

      {/* Age Rating Filter */}
      <select
        value={selectedAgeRating}
        onChange={(e) => onUpdateParams({ age_rating: e.target.value, page: null })}
        aria-label="연령 등급 선택"
        className="px-4 py-2.5 bg-dark-100 border border-white/10 rounded-lg text-white focus:outline-none focus:border-primary-500 transition"
      >
        {AGE_RATING_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      {/* Sort */}
      <select
        value={sortBy}
        onChange={(e) => onUpdateParams({ sort: e.target.value, page: null })}
        aria-label="정렬 방식"
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
        onClick={onToggleInfiniteMode}
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
      {(query || selectedGenre || selectedAgeRating) && (
        <button
          onClick={onClearFilters}
          className="px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white rounded-lg transition"
        >
          필터 초기화
        </button>
      )}
    </div>
  );
}
