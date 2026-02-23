import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "로그인 | RecFlix",
  description: "RecFlix 계정으로 로그인하고 맞춤형 영화 추천을 받아보세요.",
};

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return children;
}
