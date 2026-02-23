import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "내 프로필 | RecFlix",
  description: "내 MBTI와 계정 정보를 관리하고 추천 정확도를 높이세요.",
};

export default function ProfileLayout({ children }: { children: React.ReactNode }) {
  return children;
}
