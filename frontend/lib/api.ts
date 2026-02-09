import type {
  Movie,
  MovieDetail,
  HomeRecommendations,
  User,
  AuthTokens,
  LoginCredentials,
  SignupData,
  Genre,
  Weather,
  RatingWithMovie,
  CatchphraseResponse,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// Helper function for API calls
async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }

  return response.json();
}

// Movie APIs
export async function getMovies(params?: {
  query?: string;
  genres?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
}) {
  const searchParams = new URLSearchParams();
  if (params?.query) searchParams.set("query", params.query);
  if (params?.genres) searchParams.set("genres", params.genres);
  if (params?.page) searchParams.set("page", params.page.toString());
  if (params?.page_size) searchParams.set("page_size", params.page_size.toString());
  if (params?.sort_by) searchParams.set("sort_by", params.sort_by);

  const query = searchParams.toString();
  return fetchAPI<{ items: Movie[]; total: number; page: number; total_pages: number }>(
    `/movies${query ? `?${query}` : ""}`
  );
}

export async function getMovie(id: number): Promise<MovieDetail> {
  return fetchAPI<MovieDetail>(`/movies/${id}`);
}

export async function getSimilarMovies(id: number, limit = 10): Promise<Movie[]> {
  return fetchAPI<Movie[]>(`/movies/${id}/similar?limit=${limit}`);
}

export async function getGenres(): Promise<Genre[]> {
  return fetchAPI<Genre[]>("/movies/genres");
}

// Recommendation APIs
export async function getHomeRecommendations(weather?: string, mood?: string | null): Promise<HomeRecommendations> {
  const searchParams = new URLSearchParams();
  if (weather) searchParams.set("weather", weather);
  if (mood) searchParams.set("mood", mood);
  const query = searchParams.toString();
  return fetchAPI<HomeRecommendations>(`/recommendations${query ? `?${query}` : ""}`);
}

export async function getMBTIRecommendations(mbti: string, limit = 20): Promise<Movie[]> {
  return fetchAPI<Movie[]>(`/recommendations/mbti?mbti=${mbti}&limit=${limit}`);
}

export async function getWeatherRecommendations(weather: string, limit = 20): Promise<Movie[]> {
  return fetchAPI<Movie[]>(`/recommendations/weather?weather=${weather}&limit=${limit}`);
}

export async function getPopularMovies(limit = 20): Promise<Movie[]> {
  return fetchAPI<Movie[]>(`/recommendations/popular?limit=${limit}`);
}

// Auth APIs
export async function login(credentials: LoginCredentials): Promise<AuthTokens> {
  return fetchAPI<AuthTokens>("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export async function signup(data: SignupData): Promise<User> {
  return fetchAPI<User>("/auth/signup", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function refreshToken(refresh_token: string): Promise<AuthTokens> {
  return fetchAPI<AuthTokens>("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token }),
  });
}

// User APIs
export async function getCurrentUser(): Promise<User> {
  return fetchAPI<User>("/users/me");
}

export async function updateUser(data: Partial<User>): Promise<User> {
  return fetchAPI<User>("/users/me", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function updateMBTI(mbti: string): Promise<User> {
  return fetchAPI<User>("/users/me/mbti", {
    method: "PUT",
    body: JSON.stringify({ mbti }),
  });
}

// Rating APIs
export async function rateMovie(movieId: number, score: number, weather?: string) {
  return fetchAPI("/ratings", {
    method: "POST",
    body: JSON.stringify({
      movie_id: movieId,
      score,
      weather_context: weather,
    }),
  });
}

export async function getMyRatings(page = 1, pageSize = 20): Promise<RatingWithMovie[]> {
  return fetchAPI<RatingWithMovie[]>(`/ratings/me?page=${page}&page_size=${pageSize}`);
}

export async function deleteRating(movieId: number): Promise<void> {
  await fetchAPI(`/ratings/${movieId}`, { method: "DELETE" });
}

// Weather APIs
export async function getWeather(params?: {
  lat?: number;
  lon?: number;
  city?: string;
}): Promise<Weather> {
  const searchParams = new URLSearchParams();
  if (params?.lat !== undefined) searchParams.set("lat", params.lat.toString());
  if (params?.lon !== undefined) searchParams.set("lon", params.lon.toString());
  if (params?.city) searchParams.set("city", params.city);

  const query = searchParams.toString();
  return fetchAPI<Weather>(`/weather${query ? `?${query}` : ""}`);
}

export async function getWeatherConditions() {
  return fetchAPI<{
    conditions: Array<{
      code: string;
      name_ko: string;
      icon: string;
      description: string;
    }>;
  }>("/weather/conditions");
}

// Interaction APIs (평점/찜)
export interface MovieInteraction {
  movie_id: number;
  rating: number | null;
  is_favorited: boolean;
}

export async function getMovieInteraction(movieId: number): Promise<MovieInteraction> {
  return fetchAPI<MovieInteraction>(`/interactions/movie/${movieId}`);
}

export async function getMoviesInteractions(movieIds: number[]): Promise<{ interactions: Record<number, MovieInteraction> }> {
  return fetchAPI<{ interactions: Record<number, MovieInteraction> }>("/interactions/movies", {
    method: "POST",
    body: JSON.stringify(movieIds),
  });
}

export async function toggleFavorite(movieId: number): Promise<{ movie_id: number; is_favorited: boolean; message: string }> {
  return fetchAPI<{ movie_id: number; is_favorited: boolean; message: string }>(`/interactions/favorite/${movieId}`, {
    method: "POST",
  });
}

export async function getFavorites(page = 1, pageSize = 20): Promise<Movie[]> {
  return fetchAPI<Movie[]>(`/interactions/favorites?page=${page}&page_size=${pageSize}`);
}

export async function getPersonalizedRecommendations(limit = 20): Promise<Movie[]> {
  return fetchAPI<Movie[]>(`/recommendations/for-you?limit=${limit}`);
}

// Search Autocomplete
export interface AutocompleteResult {
  movies: Array<{
    id: number;
    title: string;
    title_en: string;
    year: number | null;
    poster_path: string | null;
  }>;
  people: Array<{
    id: number;
    name: string;
  }>;
  query: string;
}

export async function searchAutocomplete(query: string, limit = 8): Promise<AutocompleteResult> {
  return fetchAPI<AutocompleteResult>(`/movies/search/autocomplete?query=${encodeURIComponent(query)}&limit=${limit}`);
}

// LLM APIs
export async function getCatchphrase(movieId: number): Promise<CatchphraseResponse> {
  return fetchAPI<CatchphraseResponse>(`/llm/catchphrase/${movieId}`);
}
