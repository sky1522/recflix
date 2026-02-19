import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, AuthTokens, LoginCredentials, SignupData, SocialLoginResponse } from "@/types";
import * as api from "@/lib/api";
import { useInteractionStore } from "./interactionStore";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (credentials: LoginCredentials) => Promise<void>;
  signup: (data: SignupData) => Promise<void>;
  socialLogin: (response: SocialLoginResponse) => boolean;
  logout: () => void;
  fetchUser: () => Promise<void>;
  updateMBTI: (mbti: string) => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true });
        try {
          const tokens = await api.login(credentials);
          localStorage.setItem("access_token", tokens.access_token);
          localStorage.setItem("refresh_token", tokens.refresh_token);

          const user = await api.getCurrentUser();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      signup: async (data: SignupData) => {
        set({ isLoading: true });
        try {
          await api.signup(data);
          // Auto login after signup
          await get().login({ email: data.email, password: data.password });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      socialLogin: (response: SocialLoginResponse) => {
        localStorage.setItem("access_token", response.access_token);
        localStorage.setItem("refresh_token", response.refresh_token);
        set({ user: response.user, isAuthenticated: true, isLoading: false });
        return response.is_new;
      },

      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        // 상호작용 캐시 초기화
        useInteractionStore.getState().clearAll();
        set({ user: null, isAuthenticated: false });
      },

      fetchUser: async () => {
        const token = localStorage.getItem("access_token");
        if (!token) {
          set({ isAuthenticated: false, user: null });
          return;
        }

        set({ isLoading: true });
        try {
          const user = await api.getCurrentUser();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error) {
          // Token might be invalid
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },

      updateMBTI: async (mbti: string) => {
        try {
          const user = await api.updateMBTI(mbti);
          set({ user });
        } catch (error) {
          throw error;
        }
      },
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
