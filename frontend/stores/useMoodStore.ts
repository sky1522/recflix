import { create } from "zustand";
import type { MoodType } from "@/types";

interface MoodState {
  mood: MoodType | null;
  setMood: (mood: MoodType | null) => void;
}

export const useMoodStore = create<MoodState>()((set) => ({
  mood: null,
  setMood: (mood) => set({ mood }),
}));
