"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Plus, Check } from "lucide-react";
import { getImageUrl, formatRuntime, getGenreName } from "@/lib/utils";
import { getCatchphrase } from "@/lib/api";
import { trackEvent } from "@/lib/eventTracker";
import { useAuthStore } from "@/stores/authStore";
import { useInteractionStore } from "@/stores/interactionStore";
import type { Movie } from "@/types";
import MovieModal from "./MovieModal";

interface FeaturedBannerProps {
  movie: Movie;
}

export default function FeaturedBanner({ movie }: FeaturedBannerProps) {
  const router = useRouter();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isAddingToList, setIsAddingToList] = useState(false);
  const { isAuthenticated } = useAuthStore();
  const { interactions, fetchInteraction, toggleFavorite } = useInteractionStore();

  const interaction = interactions[movie.id];
  const isFavorited = interaction?.is_favorited ?? false;
  const [catchphrase, setCatchphrase] = useState<string | null>(null);

  // Fetch interaction when authenticated
  useEffect(() => {
    if (isAuthenticated && movie.id) {
      fetchInteraction(movie.id);
    }
  }, [isAuthenticated, movie.id, fetchInteraction]);

  // Fetch LLM catchphrase
  useEffect(() => {
    setCatchphrase(null);
    getCatchphrase(movie.id)
      .then((data) => setCatchphrase(data.catchphrase))
      .catch(() => {});
  }, [movie.id]);

  const handleAddToList = async () => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }

    const isAdding = !isFavorited;
    setIsAddingToList(true);
    try {
      await toggleFavorite(movie.id);
      trackEvent({
        event_type: isAdding ? "favorite_add" : "favorite_remove",
        movie_id: movie.id,
        metadata: { source: "featured_banner" },
      });
    } catch (error) {
      console.error("Failed to toggle favorite:", error);
    } finally {
      setIsAddingToList(false);
    }
  };

  return (
    <>
      <div className="relative h-[50vh] md:h-[55vh] lg:h-[60vh] w-full mb-4 md:mb-6">
        {/* Background Image */}
        <div className="absolute inset-0">
          <Image
            src={getImageUrl(movie.poster_path, "original")}
            alt={movie.title_ko || movie.title}
            fill
            className="object-cover"
            priority
          />
          {/* Gradient Overlays */}
          <div className="absolute inset-0 bg-gradient-to-r from-dark-200 via-dark-200/70 to-dark-200/30" />
          <div className="absolute inset-0 bg-gradient-to-t from-dark-200 via-transparent to-dark-200/50" />
          <div className="absolute inset-0 bg-gradient-to-b from-dark-200/60 via-transparent to-dark-200" />
        </div>

        {/* Content Container */}
        <div className="absolute inset-0 flex flex-col justify-end p-6 md:p-10 lg:p-12">
          <motion.div
            className="max-w-[85vw] md:max-w-2xl flex flex-col gap-2 md:gap-3 pb-4 md:pb-6"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            {/* Title */}
            <h1 className="flex items-baseline gap-3 whitespace-nowrap min-w-0">
              <span className="text-2xl md:text-3xl lg:text-4xl font-bold text-white leading-tight">
                {movie.title_ko || movie.title}
              </span>
              {movie.title_ko && movie.title && movie.title !== movie.title_ko && (
                <span className="text-sm md:text-base lg:text-lg text-white/40">
                  {movie.title}
                </span>
              )}
            </h1>

            {/* LLM Catchphrase */}
            {catchphrase && (
              <p className="text-sm md:text-base text-white/70 italic truncate">
                &ldquo;{catchphrase}&rdquo;
              </p>
            )}

            {/* Meta Info */}
            <div className="flex flex-wrap items-center gap-2 md:gap-3 text-sm md:text-base text-white/80">
              <div className="flex items-center space-x-1">
                <svg className="w-4 h-4 md:w-5 md:h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                <span className="font-medium">{movie.vote_average.toFixed(1)}</span>
                <span className="text-white/40 text-xs">({movie.vote_count.toLocaleString()})</span>
              </div>
              {movie.release_date && (
                <>
                  <span className="text-white/30">|</span>
                  <span>{new Date(movie.release_date).getFullYear()}</span>
                </>
              )}
              {movie.runtime && (
                <>
                  <span className="text-white/30">|</span>
                  <span>{formatRuntime(movie.runtime)}</span>
                </>
              )}
              {movie.certification && (
                <span className={`px-1.5 py-0.5 rounded text-xs font-medium border ${
                  ["ALL", "G"].includes(movie.certification.toUpperCase())
                    ? "border-green-500/50 text-green-400"
                    : ["PG", "12", "12+"].includes(movie.certification.toUpperCase())
                    ? "border-blue-500/50 text-blue-400"
                    : ["PG-13", "15", "15+"].includes(movie.certification.toUpperCase())
                    ? "border-yellow-500/50 text-yellow-400"
                    : ["R", "18", "18+", "19", "19+", "NC-17"].includes(movie.certification.toUpperCase())
                    ? "border-red-500/50 text-red-400"
                    : "border-white/30 text-white/60"
                }`}>
                  {movie.certification}
                </span>
              )}
            </div>

            {/* Genre Tags */}
            {movie.genres.length > 0 && (
              <div className="flex flex-wrap gap-1.5 md:gap-2">
                {movie.genres.slice(0, 5).map((genre, i) => (
                  <span
                    key={i}
                    className="px-2 md:px-2.5 py-0.5 md:py-1 bg-white/10 backdrop-blur-sm rounded-full text-xs md:text-sm text-white/80"
                  >
                    {getGenreName(genre)}
                  </span>
                ))}
              </div>
            )}

            {/* Buttons */}
            <div className="flex flex-wrap gap-2 sm:gap-3 mt-1">
              <Link
                href={`/movies/${movie.id}`}
                onClick={() => {
                  trackEvent({
                    event_type: "movie_click",
                    movie_id: movie.id,
                    metadata: { source: "featured_banner", section: "featured" },
                  });
                }}
                className="flex items-center space-x-2 bg-white text-black px-4 md:px-6 py-2.5 md:py-3 rounded-md font-medium hover:bg-white/90 transition text-sm md:text-base"
              >
                <svg className="w-4 h-4 md:w-5 md:h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                </svg>
                <span>상세보기</span>
              </Link>
              <button
                onClick={() => setIsModalOpen(true)}
                className="flex items-center space-x-2 bg-white/20 text-white px-4 md:px-6 py-2.5 md:py-3 rounded-md font-medium hover:bg-white/30 backdrop-blur-sm transition text-sm md:text-base"
              >
                <svg className="w-4 h-4 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <span>미리보기</span>
              </button>
              <button
                onClick={handleAddToList}
                disabled={isAddingToList}
                className={`flex items-center space-x-2 px-4 md:px-6 py-2.5 md:py-3 rounded-md font-medium transition text-sm md:text-base ${
                  isFavorited
                    ? "bg-primary-600 text-white hover:bg-primary-700"
                    : "bg-white/20 text-white hover:bg-white/30 backdrop-blur-sm"
                } ${isAddingToList ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                {isAddingToList ? (
                  <div className="w-4 h-4 md:w-5 md:h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                ) : isFavorited ? (
                  <Check className="w-4 h-4 md:w-5 md:h-5" />
                ) : (
                  <Plus className="w-4 h-4 md:w-5 md:h-5" />
                )}
                <span>{isFavorited ? "내 리스트에 추가됨" : "내 리스트"}</span>
              </button>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <MovieModal movie={movie} onClose={() => setIsModalOpen(false)} />
      )}
    </>
  );
}
