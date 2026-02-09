import { create } from "zustand";
import * as api from "@/lib/api";

interface InteractionState {
  // 영화별 상호작용 상태 캐시
  interactions: Record<number, api.MovieInteraction>;
  loading: Record<number, boolean>;

  // 액션
  fetchInteraction: (movieId: number) => Promise<api.MovieInteraction | null>;
  fetchInteractions: (movieIds: number[]) => Promise<void>;
  toggleFavorite: (movieId: number) => Promise<boolean>;
  setRating: (movieId: number, score: number) => Promise<void>;
  clearInteraction: (movieId: number) => void;
  clearAll: () => void;  // 로그아웃 시 전체 초기화
}

export const useInteractionStore = create<InteractionState>()((set, get) => ({
  interactions: {},
  loading: {},

  fetchInteraction: async (movieId: number) => {
    // 이미 로딩 중이면 스킵
    if (get().loading[movieId]) return null;

    // 캐시에 있으면 반환
    const cached = get().interactions[movieId];
    if (cached) return cached;

    set((state) => ({
      loading: { ...state.loading, [movieId]: true },
    }));

    try {
      const interaction = await api.getMovieInteraction(movieId);
      set((state) => ({
        interactions: { ...state.interactions, [movieId]: interaction },
        loading: { ...state.loading, [movieId]: false },
      }));
      return interaction;
    } catch (error) {
      // 로그인 안 된 경우 기본값
      const defaultInteraction: api.MovieInteraction = {
        movie_id: movieId,
        rating: null,
        is_favorited: false,
      };
      set((state) => ({
        interactions: { ...state.interactions, [movieId]: defaultInteraction },
        loading: { ...state.loading, [movieId]: false },
      }));
      return defaultInteraction;
    }
  },

  fetchInteractions: async (movieIds: number[]) => {
    // 캐시에 없는 것만 조회
    const uncached = movieIds.filter((id) => !get().interactions[id]);
    if (uncached.length === 0) return;

    try {
      const result = await api.getMoviesInteractions(uncached);
      set((state) => ({
        interactions: { ...state.interactions, ...result.interactions },
      }));
    } catch (error) {
      // 실패 시 기본값으로 설정
      const defaults: Record<number, api.MovieInteraction> = {};
      for (const id of uncached) {
        defaults[id] = { movie_id: id, rating: null, is_favorited: false };
      }
      set((state) => ({
        interactions: { ...state.interactions, ...defaults },
      }));
    }
  },

  toggleFavorite: async (movieId: number) => {
    const current = get().interactions[movieId];

    // Optimistic update
    set((state) => ({
      interactions: {
        ...state.interactions,
        [movieId]: {
          ...current,
          movie_id: movieId,
          rating: current?.rating ?? null,
          is_favorited: !current?.is_favorited,
        },
      },
    }));

    try {
      const result = await api.toggleFavorite(movieId);
      set((state) => ({
        interactions: {
          ...state.interactions,
          [movieId]: {
            ...state.interactions[movieId],
            is_favorited: result.is_favorited,
          },
        },
      }));
      return result.is_favorited;
    } catch (error) {
      // Rollback on error
      set((state) => ({
        interactions: {
          ...state.interactions,
          [movieId]: current || { movie_id: movieId, rating: null, is_favorited: false },
        },
      }));
      throw error;
    }
  },

  setRating: async (movieId: number, score: number) => {
    const current = get().interactions[movieId];

    // Optimistic update
    set((state) => ({
      interactions: {
        ...state.interactions,
        [movieId]: {
          ...current,
          movie_id: movieId,
          rating: score,
          is_favorited: current?.is_favorited ?? false,
        },
      },
    }));

    try {
      await api.rateMovie(movieId, score);
    } catch (error) {
      // Rollback on error
      set((state) => ({
        interactions: {
          ...state.interactions,
          [movieId]: current || { movie_id: movieId, rating: null, is_favorited: false },
        },
      }));
      throw error;
    }
  },

  clearInteraction: (movieId: number) => {
    set((state) => {
      const { [movieId]: _, ...rest } = state.interactions;
      return { interactions: rest };
    });
  },

  clearAll: () => {
    set({ interactions: {}, loading: {} });
  },
}));
