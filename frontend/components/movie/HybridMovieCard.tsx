"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import { Star, Eye } from "lucide-react";
import { getImageUrl } from "@/lib/utils";
import MovieModal from "./MovieModal";
import type { HybridMovie, RecommendationTag } from "@/types";

interface HybridMovieCardProps {
  movie: HybridMovie;
  index?: number;
  showQuickView?: boolean;
}

// Tag color mapping
const TAG_COLORS: Record<string, string> = {
  mbti: "bg-purple-500/80 text-purple-100",
  weather: "bg-blue-500/80 text-blue-100",
  personal: "bg-green-500/80 text-green-100",
  rating: "bg-yellow-500/80 text-yellow-100",
  popular: "bg-red-500/80 text-red-100",
};

function RecommendationTagBadge({ tag }: { tag: RecommendationTag }) {
  const colorClass = TAG_COLORS[tag.type] || "bg-gray-500/80 text-gray-100";

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${colorClass}`}
    >
      {tag.label}
    </span>
  );
}

export default function HybridMovieCard({ movie, index = 0, showQuickView = true }: HybridMovieCardProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [imageError, setImageError] = useState(false);

  const displayTitle = movie.title_ko || movie.title;
  const year = movie.release_date?.split("-")[0];

  // Show top 2 tags
  const displayTags = movie.recommendation_tags.slice(0, 2);

  const handleQuickView = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsModalOpen(true);
  };

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.05, duration: 0.3 }}
        className="flex-shrink-0 w-[160px] sm:w-[180px] group"
      >
        <Link href={`/movies/${movie.id}`}>
          {/* Poster Container */}
          <div className="relative aspect-[2/3] rounded-lg overflow-hidden bg-dark-100 ring-2 ring-primary-500/30 group-hover:ring-primary-500/70 transition-all duration-300 cursor-pointer">
            {movie.poster_path && !imageError ? (
              <Image
                src={getImageUrl(movie.poster_path, "w342")}
                alt={displayTitle}
                fill
                className="object-cover transition-transform duration-300 group-hover:scale-105"
                onError={() => setImageError(true)}
                sizes="(max-width: 640px) 160px, 180px"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-dark-100">
                <span className="text-white/30 text-4xl">🎬</span>
              </div>
            )}

            {/* Hover Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
              <div className="absolute bottom-0 left-0 right-0 p-3">
                {/* Rating */}
                <div className="flex items-center justify-center space-x-1 text-sm mb-2">
                  <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                  <span className="text-white font-medium">
                    {movie.vote_average.toFixed(1)}
                  </span>
                </div>

                <p className="text-sm text-white/80 text-center mb-2">상세보기</p>

                {/* Quick View Button */}
                {showQuickView && (
                  <div className="flex justify-center">
                    <button
                      onClick={handleQuickView}
                      className="flex items-center space-x-1 px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded-full text-xs text-white transition"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>미리보기</span>
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Hybrid Score Badge */}
            {movie.hybrid_score > 0 && (
              <div className="absolute top-2 right-2 bg-primary-500 text-white text-xs font-bold px-2 py-1 rounded-full">
                {Math.round(movie.hybrid_score * 100)}%
              </div>
            )}
          </div>

          {/* Info */}
          <div className="mt-2 space-y-1">
            <h3 className="text-white font-medium text-sm truncate group-hover:text-primary-400 transition">
              {displayTitle}
            </h3>

            <div className="flex items-center space-x-2 text-xs text-white/50">
              {year && <span>{year}</span>}
              {movie.genres.length > 0 && (
                <>
                  <span>|</span>
                  <span className="truncate">{typeof movie.genres[0] === 'string' ? movie.genres[0] : (movie.genres[0] as any)?.name_ko || (movie.genres[0] as any)?.name}</span>
                </>
              )}
            </div>

            {/* Recommendation Tags */}
            {displayTags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1.5">
                {displayTags.map((tag, i) => (
                  <RecommendationTagBadge key={`${tag.type}-${i}`} tag={tag} />
                ))}
              </div>
            )}
          </div>
        </Link>
      </motion.div>

      {/* Movie Modal */}
      {isModalOpen && (
        <MovieModal movie={movie} onClose={() => setIsModalOpen(false)} />
      )}
    </>
  );
}
