"use client";

import { useState, useEffect, useCallback } from "react";
import { getWeather } from "@/lib/api";
import type { Weather, WeatherType } from "@/types";

interface UseWeatherOptions {
  autoFetch?: boolean;
  defaultCity?: string;
}

interface UseWeatherReturn {
  weather: Weather | null;
  loading: boolean;
  error: string | null;
  fetchWeather: () => Promise<void>;
  fetchWeatherByCity: (city: string) => Promise<void>;
  setManualWeather: (condition: WeatherType) => void;
}

const WEATHER_CACHE_KEY = "recflix_weather";
const WEATHER_CACHE_DURATION = 30 * 60 * 1000; // 30분

interface CachedWeather {
  data: Weather;
  timestamp: number;
}

function getCachedWeather(): Weather | null {
  if (typeof window === "undefined") return null;

  try {
    const cached = localStorage.getItem(WEATHER_CACHE_KEY);
    if (!cached) return null;

    const { data, timestamp }: CachedWeather = JSON.parse(cached);
    const now = Date.now();

    if (now - timestamp < WEATHER_CACHE_DURATION) {
      return data;
    }

    localStorage.removeItem(WEATHER_CACHE_KEY);
    return null;
  } catch {
    return null;
  }
}

function setCachedWeather(weather: Weather): void {
  if (typeof window === "undefined") return;

  try {
    const cached: CachedWeather = {
      data: weather,
      timestamp: Date.now(),
    };
    localStorage.setItem(WEATHER_CACHE_KEY, JSON.stringify(cached));
  } catch {
    // 캐시 저장 실패 무시
  }
}

export function useWeather(options: UseWeatherOptions = {}): UseWeatherReturn {
  const { autoFetch = true, defaultCity = "Seoul" } = options;

  const [weather, setWeather] = useState<Weather | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWeatherByCoords = useCallback(async (lat: number, lon: number) => {
    try {
      const data = await getWeather({ lat, lon });
      setWeather(data);
      setCachedWeather(data);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch weather by coords:", err);
      throw err;
    }
  }, []);

  const fetchWeatherByCity = useCallback(async (city: string) => {
    setLoading(true);
    setError(null);

    try {
      const data = await getWeather({ city });
      setWeather(data);
      setCachedWeather(data);
    } catch (err) {
      console.error("Failed to fetch weather by city:", err);
      setError("날씨 정보를 가져올 수 없습니다");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchWeather = useCallback(async () => {
    setLoading(true);
    setError(null);

    // 캐시 확인
    const cached = getCachedWeather();
    if (cached) {
      setWeather(cached);
      setLoading(false);
      return;
    }

    // Geolocation API로 위치 가져오기
    if (typeof navigator !== "undefined" && "geolocation" in navigator) {
      try {
        const position = await new Promise<GeolocationPosition>(
          (resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
              enableHighAccuracy: false,
              timeout: 5000,
              maximumAge: 30 * 60 * 1000, // 30분 캐시
            });
          }
        );

        await fetchWeatherByCoords(
          position.coords.latitude,
          position.coords.longitude
        );
        setLoading(false);
        return;
      } catch (geoError) {
        console.log("Geolocation failed, falling back to default city:", geoError);
      }
    }

    // 위치 권한 없으면 기본 도시로 폴백
    try {
      const data = await getWeather({ city: defaultCity });
      setWeather(data);
      setCachedWeather(data);
    } catch (err) {
      console.error("Failed to fetch default weather:", err);
      setError("날씨 정보를 가져올 수 없습니다");
      // 완전 실패시 기본값 설정
      setWeather({
        condition: "sunny",
        temperature: 20,
        feels_like: 20,
        humidity: 50,
        description: "Default",
        description_ko: "맑음",
        icon: "01d",
        city: defaultCity,
        country: "KR",
        recommendation_message: "오늘의 추천 영화를 확인해보세요!",
        theme_class: "theme-sunny",
      });
    } finally {
      setLoading(false);
    }
  }, [defaultCity, fetchWeatherByCoords]);

  const setManualWeather = useCallback((condition: WeatherType) => {
    const descriptions: Record<WeatherType, string> = {
      sunny: "맑음",
      rainy: "비",
      cloudy: "흐림",
      snowy: "눈",
    };

    const messages: Record<WeatherType, string> = {
      sunny: "화창한 날씨에는 신나는 모험 영화 어떠세요?",
      rainy: "비 오는 날에는 감성적인 영화가 잘 어울려요",
      cloudy: "흐린 날에는 편안한 힐링 영화를 추천드려요",
      snowy: "눈 오는 날에는 따뜻한 로맨스 영화 어떠세요?",
    };

    const manualWeather: Weather = {
      condition,
      temperature: 20,
      feels_like: 20,
      humidity: 50,
      description: condition,
      description_ko: descriptions[condition],
      icon: condition === "sunny" ? "01d" : condition === "rainy" ? "10d" : condition === "snowy" ? "13d" : "03d",
      city: "Manual",
      country: "",
      recommendation_message: messages[condition],
      theme_class: `theme-${condition}`,
    };

    setWeather(manualWeather);
    setCachedWeather(manualWeather);
  }, []);

  useEffect(() => {
    if (autoFetch) {
      fetchWeather();
    }
  }, [autoFetch, fetchWeather]);

  return {
    weather,
    loading,
    error,
    fetchWeather,
    fetchWeatherByCity,
    setManualWeather,
  };
}
