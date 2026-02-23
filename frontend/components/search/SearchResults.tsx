"use client";

import Image from "next/image";
import { Film, User, Search, Star, Sparkles } from "lucide-react";
import type { AutocompleteResult, SemanticSearchResult } from "@/lib/api";
import { trackEvent } from "@/lib/eventTracker";
import { getImageUrl } from "@/lib/utils";
import HighlightText from "@/components/ui/HighlightText";

interface SearchResultsProps {
  query: string;
  results: AutocompleteResult | null;
  semanticResults: SemanticSearchResult[];
  isSemanticMode: boolean;
  isSemanticLoading: boolean;
  activeIndex: number;
  onMovieClick: (movieId: number) => void;
  onPersonClick: (personName: string) => void;
  onFullSearch: () => void;
  onSetActiveIndex: (index: number) => void;
}

export default function SearchResults({
  query,
  results,
  semanticResults,
  isSemanticMode,
  isSemanticLoading,
  activeIndex,
  onMovieClick,
  onPersonClick,
  onFullSearch,
  onSetActiveIndex,
}: SearchResultsProps) {
  let itemIndex = -1;

  return (
    <>
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
              const currentIdx = itemIndex;
              const isActive = currentIdx === activeIndex;
              const year = movie.release_date?.split("-")[0];
              return (
                <button
                  key={`sem-${movie.id}`}
                  id={`search-item-${currentIdx}`}
                  role="option"
                  aria-selected={isActive}
                  tabIndex={-1}
                  data-autocomplete-item
                  onClick={() => onMovieClick(movie.id)}
                  onMouseEnter={() => onSetActiveIndex(currentIdx)}
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
                    {movie.match_reason && (
                      <p className="text-purple-400/70 text-xs mt-0.5">{movie.match_reason}</p>
                    )}
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
            const currentIdx = itemIndex;
            const isActive = currentIdx === activeIndex;
            return (
              <button
                key={movie.id}
                id={`search-item-${currentIdx}`}
                role="option"
                aria-selected={isActive}
                tabIndex={-1}
                data-autocomplete-item
                onClick={() => {
                  trackEvent({
                    event_type: "search_click",
                    movie_id: movie.id,
                    metadata: { query, position: movieIdx },
                  });
                  onMovieClick(movie.id);
                }}
                onMouseEnter={() => onSetActiveIndex(currentIdx)}
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
            const currentIdx = itemIndex;
            const isActive = currentIdx === activeIndex;
            return (
              <button
                key={person.id}
                id={`search-item-${currentIdx}`}
                role="option"
                aria-selected={isActive}
                tabIndex={-1}
                data-autocomplete-item
                onClick={() => onPersonClick(person.name)}
                onMouseEnter={() => onSetActiveIndex(currentIdx)}
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
          const currentIdx = itemIndex;
          const isActive = currentIdx === activeIndex;
          return (
            <button
              id={`search-item-${currentIdx}`}
              role="option"
              aria-selected={isActive}
              tabIndex={-1}
              data-autocomplete-item
              onClick={onFullSearch}
              onMouseEnter={() => onSetActiveIndex(currentIdx)}
              className={`w-full px-4 py-3 text-primary-400 text-sm font-medium transition ${
                isActive ? "bg-primary-600/30" : "bg-primary-600/20 hover:bg-primary-600/30"
              }`}
            >
              &quot;{query}&quot; 전체 검색 결과 보기
            </button>
          );
        })()}
    </>
  );
}
