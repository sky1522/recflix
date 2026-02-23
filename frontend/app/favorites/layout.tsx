import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "찜한 영화 | RecFlix",
  description: "내가 저장한 영화 목록을 확인하고 다시 감상해보세요.",
};

export default function FavoritesLayout({ children }: { children: React.ReactNode }) {
  return children;
}
