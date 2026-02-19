"use client";

import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Star,
  Heart,
  Clock,
  Calendar,
  ArrowLeft,
  Play,
} from "lucide-react";
import { getImageUrl, formatRuntime, formatDate } from "@/lib/utils";
import type { MovieDetail } from "@/types";

interface MovieHeroProps {
  movie: MovieDetail;
  displayTitle: string;
  catchphrase: string | null;
  catchphraseLoading: boolean;
  isFavorited: boolean;
  onBack: () => void;
  onFavoriteClick: () => void;
}

export default function MovieHero({
  movie,
  displayTitle,
  catchphrase,
  catchphraseLoading,
  isFavorited,
  onBack,
  onFavoriteClick,
}: MovieHeroProps) {
  return (
    <div className="relative h-[60vh] md:h-[70vh]">
      {/* Backdrop Image */}
      <div className="absolute inset-0">
        {movie.poster_path ? (
          <Image
            src={getImageUrl(movie.poster_path, "original")}
            alt={displayTitle}
            fill
            className="object-cover object-top"
            priority
          />
        ) : (
          <div className="w-full h-full bg-dark-100" />
        )}
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-dark-200 via-dark-200/70 to-dark-200/30" />
        <div className="absolute inset-0 bg-gradient-to-r from-dark-200/90 via-transparent to-transparent" />
      </div>

      {/* Back Button */}
      <motion.button
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        onClick={onBack}
        className="absolute top-4 left-4 md:left-8 z-10 flex items-center space-x-2 px-3 py-2 bg-black/50 hover:bg-black/70 rounded-full text-white transition"
      >
        <ArrowLeft className="w-5 h-5" />
        <span className="hidden sm:inline text-sm">뒤로</span>
      </motion.button>

      {/* Hero Content */}
      <div className="absolute bottom-0 left-0 right-0 p-4 md:p-8 lg:p-12">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row gap-4 md:gap-8">
          {/* Mobile Poster */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="md:hidden flex-shrink-0 w-28 sm:w-32"
          >
            <div className="relative aspect-[2/3] rounded-lg overflow-hidden shadow-2xl">
              {movie.poster_path ? (
                <Image
                  src={getImageUrl(movie.poster_path, "w342")}
                  alt={displayTitle}
                  fill
                  className="object-cover"
                />
              ) : (
                <div className="w-full h-full bg-dark-100 flex items-center justify-center">
                  <span className="text-4xl">🎬</span>
                </div>
              )}
            </div>
          </motion.div>

          {/* Desktop Poster */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="hidden md:block flex-shrink-0 w-64 lg:w-72"
          >
            <div className="relative aspect-[2/3] rounded-lg overflow-hidden shadow-2xl">
              {movie.poster_path ? (
                <Image
                  src={getImageUrl(movie.poster_path, "w500")}
                  alt={displayTitle}
                  fill
                  className="object-cover"
                />
              ) : (
                <div className="w-full h-full bg-dark-100 flex items-center justify-center">
                  <span className="text-6xl">🎬</span>
                </div>
              )}
            </div>
          </motion.div>

          {/* Info */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="flex-1 min-w-0"
          >
            {/* Title */}
            <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-1 md:mb-2 line-clamp-2">
              {displayTitle}
            </h1>

            {/* Original Title */}
            {movie.title_ko && movie.title !== movie.title_ko && (
              <p className="text-white/60 text-sm md:text-lg mb-2 md:mb-4 truncate">{movie.title}</p>
            )}

            {/* Catchphrase */}
            <div className="mb-3 sm:mb-4">
              {catchphraseLoading ? (
                <div className="h-6 sm:h-7 w-48 sm:w-64 bg-white/10 animate-pulse rounded" />
              ) : (catchphrase || movie.tagline) && (
                <p className="text-white/80 italic text-sm sm:text-base md:text-lg line-clamp-2">
                  &quot;{catchphrase || movie.tagline}&quot;
                </p>
              )}
            </div>

            {/* Meta Info */}
            <div className="flex flex-wrap items-center gap-2 md:gap-4 text-xs sm:text-sm md:text-base text-white/70 mb-4 md:mb-6">
              <div className="flex items-center space-x-1 text-yellow-400">
                <Star className="w-4 h-4 md:w-5 md:h-5 fill-current" />
                <span className="font-semibold">{movie.vote_average.toFixed(1)}</span>
                <span className="text-white/50 hidden sm:inline">({movie.vote_count.toLocaleString()})</span>
              </div>
              {movie.release_date && (
                <div className="flex items-center space-x-1">
                  <Calendar className="w-3.5 h-3.5 md:w-4 md:h-4" />
                  <span>{formatDate(movie.release_date)}</span>
                </div>
              )}
              {movie.runtime && (
                <div className="flex items-center space-x-1">
                  <Clock className="w-3.5 h-3.5 md:w-4 md:h-4" />
                  <span>{formatRuntime(movie.runtime)}</span>
                </div>
              )}
              {movie.certification && (
                <span className="px-1.5 md:px-2 py-0.5 border border-white/30 rounded text-xs">
                  {movie.certification}
                </span>
              )}
            </div>

            {/* Genres */}
            <div className="flex flex-wrap gap-1.5 md:gap-2 mb-4 md:mb-6">
              {movie.genres.slice(0, 4).map((genre, index) => {
                const genreName = typeof genre === 'string' ? genre : (genre as any).name_ko || (genre as any).name;
                return (
                  <Link
                    key={genreName || index}
                    href={`/movies?genre=${encodeURIComponent(genreName)}`}
                    className="px-2 md:px-3 py-1 bg-white/10 hover:bg-white/20 rounded-full text-xs md:text-sm text-white/80 transition"
                  >
                    {genreName}
                  </Link>
                );
              })}
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-2 md:gap-3">
              <button className="flex items-center space-x-1.5 md:space-x-2 px-4 md:px-6 py-2.5 md:py-3 bg-primary-600 hover:bg-primary-700 active:bg-primary-800 text-white font-medium rounded-lg transition text-sm md:text-base">
                <Play className="w-4 h-4 md:w-5 md:h-5 fill-white" />
                <span>시청하기</span>
              </button>
              <button
                onClick={onFavoriteClick}
                className={`flex items-center space-x-1.5 md:space-x-2 px-4 md:px-6 py-2.5 md:py-3 rounded-lg font-medium transition text-sm md:text-base ${
                  isFavorited
                    ? "bg-red-500 hover:bg-red-600 active:bg-red-700 text-white"
                    : "bg-white/10 hover:bg-white/20 active:bg-white/30 text-white"
                }`}
              >
                <Heart className={`w-4 h-4 md:w-5 md:h-5 ${isFavorited ? "fill-current" : ""}`} />
                <span>{isFavorited ? "찜 완료" : "찜하기"}</span>
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
