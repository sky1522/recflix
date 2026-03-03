"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { getPopularityScore } from "@/lib/utils";
import type { MovieDetail } from "@/types";

const WEATHER_EMOJI: Record<string, string> = {
  sunny: "☀️",
  rainy: "🌧️",
  cloudy: "☁️",
  snowy: "❄️",
};

const WEATHER_LABEL: Record<string, string> = {
  sunny: "맑은 날",
  rainy: "비 오는 날",
  cloudy: "흐린 날",
  snowy: "눈 오는 날",
};

interface MovieSidebarProps {
  movie: MovieDetail;
}

export default function MovieSidebar({ movie }: MovieSidebarProps) {
  const pop = getPopularityScore(movie.popularity);

  return (
    <motion.aside
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3 }}
      className="space-y-6"
    >
      {/* Movie Info Card */}
      <div className="p-6 bg-dark-100 rounded-lg space-y-5">
        <h3 className="text-lg font-semibold text-white">영화 정보</h3>

        {/* Countries */}
        {(movie.countries && movie.countries.length > 0) && (
          <div>
            <p className="text-white/50 text-sm mb-2">🌍 제작 국가</p>
            <div className="flex flex-wrap gap-1.5">
              {movie.countries.map((c) => (
                <Link
                  key={c}
                  href={`/movies?country=${encodeURIComponent(c)}`}
                  className="px-2 py-1 bg-dark-200 rounded text-xs text-white/70 hover:bg-white/20 hover:text-white transition cursor-pointer"
                >
                  {c}
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Keywords */}
        {movie.keywords && movie.keywords.length > 0 && (
          <div>
            <p className="text-white/50 text-sm mb-2">🏷️ 키워드</p>
            <div className="flex flex-wrap gap-1.5">
              {movie.keywords.slice(0, 10).map((keyword) => (
                <Link
                  key={keyword}
                  href={`/movies?keyword=${encodeURIComponent(keyword)}`}
                  className="px-2 py-1 bg-dark-200 rounded text-xs text-white/70 hover:bg-violet-600/30 hover:text-violet-300 transition cursor-pointer"
                >
                  {keyword}
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Popularity */}
        <div>
          <p className="text-white/50 text-sm mb-2">📈 인기도</p>
          <p className="text-white/80 text-sm">
            {pop.emoji}{pop.emoji && " "}
            {pop.score.toFixed(1)} / 10
            {pop.label && <span className="text-white/50"> · {pop.label}</span>}
          </p>
        </div>
      </div>

      {/* MBTI Scores */}
      {movie.mbti_scores && Object.keys(movie.mbti_scores).length > 0 && (
        <div className="p-6 bg-dark-100 rounded-lg space-y-5">
          <h3 className="text-lg font-semibold text-white">MBTI 추천 점수</h3>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(movie.mbti_scores)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 4)
              .map(([mbti, score]) => (
                <Link
                  key={mbti}
                  href={`/movies?mbti=${mbti}`}
                  title={`${mbti} 추천 영화 보기`}
                  className="flex items-center justify-between p-2 bg-dark-200 rounded hover:bg-amber-600/20 transition cursor-pointer"
                >
                  <span className="text-white/80 text-sm font-medium">{mbti}</span>
                  <span className="text-primary-400 text-sm">
                    {(Number(score) * 100).toFixed(0)}%
                  </span>
                </Link>
              ))}
          </div>
        </div>
      )}

      {/* Weather Scores */}
      {movie.weather_scores && Object.keys(movie.weather_scores).length > 0 && (
        <div className="p-6 bg-dark-100 rounded-lg space-y-5">
          <h3 className="text-lg font-semibold text-white">날씨별 추천</h3>
          <div className="space-y-2">
            {Object.entries(movie.weather_scores)
              .sort(([, a], [, b]) => b - a)
              .map(([w, score]) => (
                <Link
                  key={w}
                  href={`/movies?weather=${w}`}
                  title={`${WEATHER_LABEL[w]} 추천 영화 보기`}
                  className="flex items-center justify-between p-2 bg-dark-200 rounded hover:bg-sky-600/20 transition cursor-pointer"
                >
                  <span className="text-white/80 text-sm">
                    {WEATHER_EMOJI[w]} {WEATHER_LABEL[w]}
                  </span>
                  <span className="text-blue-400 text-sm">
                    {(Number(score) * 100).toFixed(0)}%
                  </span>
                </Link>
              ))}
          </div>
        </div>
      )}
    </motion.aside>
  );
}
