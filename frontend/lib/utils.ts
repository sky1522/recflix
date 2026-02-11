import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getImageUrl(path: string | null, size: string = "w500"): string {
  if (!path) {
    return "/placeholder-movie.png";
  }
  return `https://image.tmdb.org/t/p/${size}${path}`;
}

export function formatRuntime(minutes: number | null): string {
  if (!minutes) return "";
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
}

export function formatDate(dateString: string | null): string {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.getFullYear().toString();
}

/**
 * Convert TMDB popularity to log-scale 0-10 score
 * Based on 42,917 movies: min=0.007, max=728
 */
export function getPopularityScore(popularity: number): {
  score: number;
  label: string | null;
  emoji: string;
} {
  const MIN_POP = 0.007;
  const MAX_POP = 728;
  const clamped = Math.max(MIN_POP, Math.min(MAX_POP, popularity));
  const score = Math.round(
    ((Math.log(clamped) - Math.log(MIN_POP)) / (Math.log(MAX_POP) - Math.log(MIN_POP))) * 100
  ) / 10;

  if (score >= 8.0) return { score, label: "초화제작", emoji: "\uD83D\uDD25\uD83D\uDD25\uD83D\uDD25" };
  if (score >= 6.5) return { score, label: "인기작", emoji: "\uD83D\uDD25\uD83D\uDD25" };
  if (score >= 5.0) return { score, label: "주목작", emoji: "\uD83D\uDD25" };
  return { score, label: null, emoji: "" };
}

export function getWeatherEmoji(weather: string): string {
  const emojis: Record<string, string> = {
    sunny: "☀️",
    rainy: "🌧️",
    cloudy: "☁️",
    snowy: "❄️",
  };
  return emojis[weather] || "🌤️";
}

export function getMBTIColor(mbti: string): string {
  const colors: Record<string, string> = {
    // Analysts - Purple
    INTJ: "bg-purple-600",
    INTP: "bg-purple-500",
    ENTJ: "bg-purple-700",
    ENTP: "bg-purple-400",
    // Diplomats - Green
    INFJ: "bg-green-600",
    INFP: "bg-green-500",
    ENFJ: "bg-green-700",
    ENFP: "bg-green-400",
    // Sentinels - Blue
    ISTJ: "bg-blue-600",
    ISFJ: "bg-blue-500",
    ESTJ: "bg-blue-700",
    ESFJ: "bg-blue-400",
    // Explorers - Yellow
    ISTP: "bg-yellow-600",
    ISFP: "bg-yellow-500",
    ESTP: "bg-yellow-700",
    ESFP: "bg-yellow-400",
  };
  return colors[mbti] || "bg-gray-600";
}
