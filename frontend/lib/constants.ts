// 캐시 키
export const WEATHER_CACHE_KEY = "recflix_weather_v3";
export const WEATHER_CACHE_DURATION = 30 * 60 * 1000; // 30분

// 큐레이션 문구 개수
export const SUBTITLE_COUNT = 6;

// 날씨 테마 클래스
export const WEATHER_THEME_CLASSES = [
  "theme-sunny",
  "theme-rainy",
  "theme-cloudy",
  "theme-snowy",
] as const;
