import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "내 평점 | RecFlix",
  description: "평가한 영화와 평균 평점을 확인하고 취향을 관리하세요.",
};

export default function RatingsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
