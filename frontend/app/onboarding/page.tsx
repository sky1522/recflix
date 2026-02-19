"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { Star, ChevronRight, Check } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import * as api from "@/lib/api";
import type { Movie } from "@/types";

const GENRE_OPTIONS = [
  "액션", "로맨스", "코미디", "공포", "스릴러",
  "SF", "드라마", "애니메이션", "범죄", "판타지",
] as const;

const MIN_GENRES = 3;
const MIN_RATINGS = 10;

export default function OnboardingPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [step, setStep] = useState<"genres" | "movies">("genres");
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [movies, setMovies] = useState<Movie[]>([]);
  const [ratings, setRatings] = useState<Record<number, number>>({});
  const [loadingMovies, setLoadingMovies] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, router]);

  const toggleGenre = (genre: string) => {
    setSelectedGenres((prev) =>
      prev.includes(genre) ? prev.filter((g) => g !== genre) : [...prev, genre]
    );
  };

  const goToMovies = async () => {
    setLoadingMovies(true);
    try {
      const data = await api.getOnboardingMovies();
      setMovies(data);
      setStep("movies");
    } catch {
      setMovies([]);
      setStep("movies");
    } finally {
      setLoadingMovies(false);
    }
  };

  const handleRate = async (movieId: number, score: number) => {
    setRatings((prev) => ({ ...prev, [movieId]: score }));
    try {
      await api.rateMovie(movieId, score);
    } catch {
      // silent fail - rating is visually shown
    }
  };

  const handleComplete = async () => {
    setSubmitting(true);
    try {
      await api.completeOnboarding(selectedGenres);
      router.replace("/");
    } catch {
      router.replace("/");
    }
  };

  const handleSkip = () => {
    router.replace("/");
  };

  const ratedCount = Object.keys(ratings).length;

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-dark-200 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Progress indicator */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div
            className={`w-3 h-3 rounded-full ${
              step === "genres" ? "bg-primary-500" : "bg-primary-500/40"
            }`}
          />
          <div className="w-12 h-0.5 bg-white/10" />
          <div
            className={`w-3 h-3 rounded-full ${
              step === "movies" ? "bg-primary-500" : "bg-white/20"
            }`}
          />
        </div>

        <AnimatePresence mode="wait">
          {step === "genres" ? (
            <GenreStep
              key="genres"
              selectedGenres={selectedGenres}
              toggleGenre={toggleGenre}
              onNext={goToMovies}
              onSkip={handleSkip}
              loading={loadingMovies}
            />
          ) : (
            <MovieStep
              key="movies"
              movies={movies}
              ratings={ratings}
              ratedCount={ratedCount}
              onRate={handleRate}
              onComplete={handleComplete}
              onSkip={handleSkip}
              submitting={submitting}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function GenreStep({
  selectedGenres,
  toggleGenre,
  onNext,
  onSkip,
  loading,
}: {
  selectedGenres: string[];
  toggleGenre: (genre: string) => void;
  onNext: () => void;
  onSkip: () => void;
  loading: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="text-center"
    >
      <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
        좋아하는 장르를 선택해주세요
      </h1>
      <p className="text-white/50 mb-8">
        {MIN_GENRES}개 이상 선택하면 더 정확한 추천을 받을 수 있어요
      </p>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 max-w-2xl mx-auto mb-8">
        {GENRE_OPTIONS.map((genre) => {
          const selected = selectedGenres.includes(genre);
          return (
            <button
              key={genre}
              onClick={() => toggleGenre(genre)}
              className={`relative py-4 px-3 rounded-xl font-medium transition-all ${
                selected
                  ? "bg-primary-600 text-white ring-2 ring-primary-400"
                  : "bg-dark-100 text-white/70 hover:bg-dark-100/80 hover:text-white"
              }`}
            >
              {selected && (
                <Check className="absolute top-2 right-2 w-4 h-4" />
              )}
              {genre}
            </button>
          );
        })}
      </div>

      <div className="flex flex-col items-center gap-3">
        <button
          onClick={onNext}
          disabled={selectedGenres.length < MIN_GENRES || loading}
          className="px-8 py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-white/10 disabled:text-white/30 text-white font-medium rounded-lg transition flex items-center gap-2"
        >
          {loading ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              불러오는 중...
            </>
          ) : (
            <>
              다음
              <ChevronRight className="w-5 h-5" />
            </>
          )}
        </button>
        <button
          onClick={onSkip}
          className="text-white/40 hover:text-white/60 text-sm transition"
        >
          건너뛰기
        </button>
      </div>
    </motion.div>
  );
}

function MovieStep({
  movies,
  ratings,
  ratedCount,
  onRate,
  onComplete,
  onSkip,
  submitting,
}: {
  movies: Movie[];
  ratings: Record<number, number>;
  ratedCount: number;
  onRate: (movieId: number, score: number) => void;
  onComplete: () => void;
  onSkip: () => void;
  submitting: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
    >
      <div className="text-center mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
          영화를 평가해주세요
        </h1>
        <p className="text-white/50">
          최소 {MIN_RATINGS}편을 평가하면 맞춤 추천이 시작됩니다
        </p>
      </div>

      {/* Progress bar */}
      <div className="max-w-md mx-auto mb-8">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-white/60">
            <span className="text-primary-400 font-bold">{ratedCount}</span>/{MIN_RATINGS}편 평가 완료
          </span>
          {ratedCount >= MIN_RATINGS && (
            <span className="text-green-400 text-sm">완료!</span>
          )}
        </div>
        <div className="h-2 bg-dark-100 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-primary-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(100, (ratedCount / MIN_RATINGS) * 100)}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </div>

      {/* Movie grid */}
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-3 md:gap-4 mb-8">
        {movies.map((movie) => (
          <OnboardingMovieCard
            key={movie.id}
            movie={movie}
            rating={ratings[movie.id]}
            onRate={(score) => onRate(movie.id, score)}
          />
        ))}
      </div>

      {/* Actions */}
      <div className="flex flex-col items-center gap-3 pb-8">
        <button
          onClick={onComplete}
          disabled={ratedCount < MIN_RATINGS || submitting}
          className="px-8 py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-white/10 disabled:text-white/30 text-white font-medium rounded-lg transition flex items-center gap-2"
        >
          {submitting ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              처리 중...
            </>
          ) : (
            "RecFlix 시작하기"
          )}
        </button>
        <button
          onClick={onSkip}
          className="text-white/40 hover:text-white/60 text-sm transition"
        >
          건너뛰기
        </button>
      </div>
    </motion.div>
  );
}

function OnboardingMovieCard({
  movie,
  rating,
  onRate,
}: {
  movie: Movie;
  rating?: number;
  onRate: (score: number) => void;
}) {
  const [hoverStar, setHoverStar] = useState(0);
  const displayTitle = movie.title_ko || movie.title;

  return (
    <div className="flex flex-col">
      <div className="relative aspect-[2/3] rounded-lg overflow-hidden bg-dark-100 mb-1.5">
        {movie.poster_path ? (
          <Image
            src={`https://image.tmdb.org/t/p/w300${movie.poster_path}`}
            alt={displayTitle}
            fill
            className="object-cover"
            sizes="(max-width: 640px) 33vw, (max-width: 768px) 25vw, 20vw"
            unoptimized
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-white/20 text-xs">
            No Image
          </div>
        )}
        {rating && (
          <div className="absolute top-1 right-1 bg-primary-600 text-white text-xs px-1.5 py-0.5 rounded font-bold">
            {rating}
          </div>
        )}
      </div>
      <p className="text-white text-xs leading-tight line-clamp-2 mb-1">
        {displayTitle}
      </p>
      {/* Star rating */}
      <div className="flex gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => onRate(star)}
            onMouseEnter={() => setHoverStar(star)}
            onMouseLeave={() => setHoverStar(0)}
            className="p-0"
          >
            <Star
              className={`w-3.5 h-3.5 transition-colors ${
                star <= (hoverStar || rating || 0)
                  ? "fill-yellow-400 text-yellow-400"
                  : "text-white/20"
              }`}
            />
          </button>
        ))}
      </div>
    </div>
  );
}
