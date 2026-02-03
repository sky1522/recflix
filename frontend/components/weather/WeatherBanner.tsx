"use client";

import { motion } from "framer-motion";
import type { Weather, WeatherType } from "@/types";

interface WeatherBannerProps {
  weather: Weather;
  onWeatherChange?: (condition: WeatherType) => void;
  showSelector?: boolean;
}

const weatherEmojis: Record<WeatherType, string> = {
  sunny: "\u2600\ufe0f",
  rainy: "\ud83c\udf27\ufe0f",
  cloudy: "\u2601\ufe0f",
  snowy: "\u2744\ufe0f",
};

const weatherGradients: Record<WeatherType, string> = {
  sunny: "from-amber-400 via-orange-300 to-yellow-200",
  rainy: "from-slate-600 via-blue-400 to-slate-500",
  cloudy: "from-gray-400 via-slate-300 to-gray-200",
  snowy: "from-blue-100 via-white to-blue-50",
};

const weatherTextColors: Record<WeatherType, string> = {
  sunny: "text-amber-900",
  rainy: "text-white",
  cloudy: "text-gray-800",
  snowy: "text-blue-900",
};

const weatherLabels: Record<WeatherType, string> = {
  sunny: "맑음",
  rainy: "비",
  cloudy: "흐림",
  snowy: "눈",
};

export default function WeatherBanner({
  weather,
  onWeatherChange,
  showSelector = false,
}: WeatherBannerProps) {
  const condition = weather.condition;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={`relative overflow-hidden rounded-xl md:rounded-2xl bg-gradient-to-r ${weatherGradients[condition]} p-4 md:p-6 shadow-lg`}
    >
      {/* Background decoration */}
      <div className="absolute inset-0 opacity-20">
        {condition === "rainy" && <RainAnimation />}
        {condition === "snowy" && <SnowAnimation />}
        {condition === "sunny" && <SunAnimation />}
      </div>

      <div className="relative z-10">
        {/* Main content - responsive layout */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
          {/* Weather info */}
          <div className="flex items-center gap-3 md:gap-4">
            <div className={`text-4xl md:text-5xl ${weatherTextColors[condition]}`}>
              {weatherEmojis[condition]}
            </div>
            <div>
              <div className={`text-xl md:text-2xl font-bold ${weatherTextColors[condition]}`}>
                {weather.temperature}°C
              </div>
              <div className={`text-xs md:text-sm ${weatherTextColors[condition]} opacity-80`}>
                {weather.city} · {weather.description_ko}
              </div>
            </div>
          </div>

          {/* Recommendation message */}
          <div className={`${weatherTextColors[condition]} sm:text-right`}>
            <p className="text-sm md:text-lg font-medium leading-snug">
              {weather.recommendation_message}
            </p>
          </div>
        </div>

        {/* Weather selector */}
        {showSelector && onWeatherChange && (
          <div className="mt-4 flex flex-wrap gap-2">
            {(["sunny", "rainy", "cloudy", "snowy"] as WeatherType[]).map((w) => (
              <button
                key={w}
                onClick={() => onWeatherChange(w)}
                className={`rounded-full px-3 py-1.5 md:px-4 md:py-2 text-xs md:text-sm font-medium transition-all ${
                  condition === w
                    ? "bg-white/30 shadow-md"
                    : "bg-white/10 hover:bg-white/20"
                } ${weatherTextColors[condition]}`}
              >
                {weatherEmojis[w]} {weatherLabels[w]}
              </button>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

// Rain animation component
function RainAnimation() {
  return (
    <div className="absolute inset-0">
      {[...Array(15)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute h-6 md:h-8 w-0.5 bg-blue-300/50"
          initial={{
            x: Math.random() * 100 + "%",
            y: -20,
          }}
          animate={{
            y: "120%",
          }}
          transition={{
            duration: 0.8 + Math.random() * 0.4,
            repeat: Infinity,
            delay: Math.random() * 2,
            ease: "linear",
          }}
        />
      ))}
    </div>
  );
}

// Snow animation component
function SnowAnimation() {
  return (
    <div className="absolute inset-0">
      {[...Array(20)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute h-1.5 w-1.5 md:h-2 md:w-2 rounded-full bg-white/70"
          initial={{
            x: Math.random() * 100 + "%",
            y: -10,
          }}
          animate={{
            y: "120%",
            x: `${Math.random() * 100}%`,
          }}
          transition={{
            duration: 3 + Math.random() * 2,
            repeat: Infinity,
            delay: Math.random() * 3,
            ease: "linear",
          }}
        />
      ))}
    </div>
  );
}

// Sun animation component
function SunAnimation() {
  return (
    <motion.div
      className="absolute -right-5 -top-5 md:-right-10 md:-top-10 h-24 w-24 md:h-40 md:w-40 rounded-full bg-yellow-300/30"
      animate={{
        scale: [1, 1.1, 1],
        opacity: [0.3, 0.5, 0.3],
      }}
      transition={{
        duration: 3,
        repeat: Infinity,
        ease: "easeInOut",
      }}
    />
  );
}

// Compact weather indicator for header
export function WeatherIndicator({ weather }: { weather: Weather }) {
  return (
    <div className="flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 backdrop-blur-sm">
      <span className="text-lg">{weatherEmojis[weather.condition]}</span>
      <span className="text-sm font-medium text-white">
        {weather.temperature}°C
      </span>
    </div>
  );
}
