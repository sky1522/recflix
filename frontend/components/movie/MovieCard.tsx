"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import { Star, Eye } from "lucide-react";
import { getImageUrl, formatDate } from "@/lib/utils";
import { trackEvent } from "@/lib/eventTracker";
import type { Movie } from "@/types";
import MovieModal from "./MovieModal";
import HighlightText from "@/components/ui/HighlightText";

const CERT_BADGE_COLORS: Record<string, string> = {
  ALL: "bg-green-600",
  G: "bg-green-600",
  PG: "bg-blue-600",
  "12": "bg-blue-600",
  "PG-13": "bg-yellow-600",
  "15": "bg-yellow-600",
  R: "bg-red-600",
  "18": "bg-red-600",
  "19": "bg-red-600",
  "NC-17": "bg-red-600",
};

interface MovieCardProps {
  movie: Movie;
  index?: number;
  showQuickView?: boolean;
  highlightQuery?: string;
  section?: string;
}

export default function MovieCard({ movie, index = 0, showQuickView = true, highlightQuery = "", section }: MovieCardProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [imageError, setImageError] = useState(false);

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
        transition={{ duration: 0.3, delay: index * 0.05 }}
        className="flex-shrink-0 w-[160px] md:w-[200px] group"
      >
        <Link
          href={`/movies/${movie.id}`}
          onClick={() => {
            if (section) {
              trackEvent({
                event_type: "movie_click",
                movie_id: movie.id,
                metadata: { source: "recommendation", section, position: index },
              });
            }
          }}
        >
          {/* Poster */}
          <div className="relative aspect-[2/3] rounded-md overflow-hidden bg-dark-100 cursor-pointer">
            {!imageError && movie.poster_path ? (
              <Image
                src={getImageUrl(movie.poster_path, "w342")}
                alt={movie.title_ko || movie.title}
                fill
                className="object-cover transition-transform duration-300 group-hover:scale-105"
                onError={() => setImageError(true)}
                sizes="(max-width: 768px) 160px, 200px"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-dark-100">
                <svg className="w-12 h-12 text-white/20" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18 4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4h-4z" />
                </svg>
              </div>
            )}

            {/* Certification badge */}
            {movie.certification && CERT_BADGE_COLORS[movie.certification] && (
              <span className={`absolute top-1.5 left-1.5 px-1.5 py-0.5 text-[10px] font-bold text-white rounded ${CERT_BADGE_COLORS[movie.certification]} z-10`}>
                {movie.certification}
              </span>
            )}

            {/* Hover overlay */}
            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col items-center justify-center">
              <div className="text-center p-4">
                <div className="flex items-center justify-center space-x-1 text-yellow-400 mb-2">
                  <Star className="w-5 h-5 fill-current" />
                  <span className="font-medium">{movie.vote_average.toFixed(1)}</span>
                </div>
                <p className="text-sm text-white/80 mb-3">상세보기</p>

                {/* Quick View Button */}
                {showQuickView && (
                  <button
                    onClick={handleQuickView}
                    className="flex items-center space-x-1 px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded-full text-xs text-white transition"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>미리보기</span>
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Info - 중앙 정렬 */}
          <div className="mt-2 px-1 text-center">
            <h3 className="text-sm font-medium text-white truncate group-hover:text-primary-400 transition">
              {highlightQuery ? (
                <HighlightText text={movie.title_ko || movie.title} query={highlightQuery} />
              ) : (
                movie.title_ko || movie.title
              )}
            </h3>
            <div className="flex items-center justify-center gap-1.5 text-xs text-white/50 mt-1">
              <span>{formatDate(movie.release_date)}</span>
              {movie.genres.length > 0 && (
                <>
                  <span>·</span>
                  <span className="truncate">{typeof movie.genres[0] === 'string' ? movie.genres[0] : (movie.genres[0] as any)?.name_ko || (movie.genres[0] as any)?.name}</span>
                </>
              )}
            </div>
          </div>
        </Link>
      </motion.div>

      {/* Modal */}
      {isModalOpen && (
        <MovieModal movie={movie} onClose={() => setIsModalOpen(false)} />
      )}
    </>
  );
}
