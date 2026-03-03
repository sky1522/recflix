"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

type Theme = "dark" | "light";

interface ThemeState {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

function applyThemeClass(theme: Theme) {
  if (typeof document === "undefined") return;
  const html = document.documentElement;
  if (theme === "light") {
    html.classList.add("light");
  } else {
    html.classList.remove("light");
  }
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: "dark",

      toggleTheme: () =>
        set((state) => {
          const next: Theme = state.theme === "dark" ? "light" : "dark";
          applyThemeClass(next);
          return { theme: next };
        }),

      setTheme: (theme: Theme) => {
        applyThemeClass(theme);
        set({ theme });
      },
    }),
    {
      name: "theme-storage",
      onRehydrateStorage: () => (state) => {
        if (state) applyThemeClass(state.theme);
      },
    }
  )
);
