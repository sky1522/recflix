// Movie types
export interface Movie {
  id: number;
  title: string;
  title_ko: string | null;
  certification: string | null;
  runtime: number | null;
  vote_average: number;
  vote_count: number;
  popularity: number;
  poster_path: string | null;
  release_date: string | null;
  is_adult: boolean;
  genres: string[];
}

export interface MovieDetail extends Movie {
  overview: string | null;
  overview_ko: string | null;
  tagline: string | null;
  overview_lang: string | null;
  cast_members: Person[];
  keywords: string[];
  countries: string[];
  mbti_scores: Record<string, number> | null;
  weather_scores: Record<string, number> | null;
  emotion_tags: Record<string, number> | null;
}

export interface Genre {
  id: number;
  name: string;
  name_ko: string | null;
}

export interface Person {
  id: number;
  name: string;
}

// Recommendation types
export interface RecommendationTag {
  type: "mbti" | "weather" | "personal" | "popular" | "rating";
  label: string;
  score?: number;
}

export interface HybridMovie extends Movie {
  recommendation_tags: RecommendationTag[];
  hybrid_score: number;
}

export interface RecommendationRow {
  title: string;
  description: string | null;
  movies: Movie[];
}

export interface HybridRecommendationRow {
  title: string;
  description: string | null;
  movies: HybridMovie[];
}

export interface HomeRecommendations {
  featured: Movie | null;
  rows: RecommendationRow[];
  hybrid_row?: HybridRecommendationRow | null;
}

// User types
export interface User {
  id: number;
  email: string;
  nickname: string;
  mbti: string | null;
  birth_date: string | null;
  location_consent: boolean;
  is_active: boolean;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupData {
  email: string;
  password: string;
  nickname: string;
  mbti?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Collection types
export interface Collection {
  id: number;
  user_id: number;
  name: string;
  description: string | null;
  is_public: boolean;
  created_at: string;
  movie_count: number;
}

// Rating types
export interface Rating {
  id: number;
  user_id: number;
  movie_id: number;
  score: number;
  weather_context: string | null;
  created_at: string;
}

export interface RatingWithMovie extends Rating {
  movie: Movie;
}

// Weather types
export type WeatherType = "sunny" | "rainy" | "cloudy" | "snowy";

export interface Weather {
  condition: WeatherType;
  temperature: number;
  feels_like: number;
  humidity: number;
  description: string;
  description_ko: string;
  icon: string;
  city: string;
  country: string;
  recommendation_message: string;
  theme_class: string;
}

// MBTI types
export type MBTIType =
  | "INTJ" | "INTP" | "ENTJ" | "ENTP"
  | "INFJ" | "INFP" | "ENFJ" | "ENFP"
  | "ISTJ" | "ISFJ" | "ESTJ" | "ESFJ"
  | "ISTP" | "ISFP" | "ESTP" | "ESFP";

// LLM types
export interface CatchphraseResponse {
  movie_id: number;
  catchphrase: string;
  cached: boolean;
}
