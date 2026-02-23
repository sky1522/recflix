import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "취향 설정 | RecFlix",
  description: "선호 장르와 초기 평점을 통해 개인화 추천을 시작하세요.",
};

export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  return children;
}
