import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "회원가입 | RecFlix",
  description: "MBTI·날씨·기분 기반 추천을 위한 RecFlix 계정을 생성하세요.",
};

export default function SignupLayout({ children }: { children: React.ReactNode }) {
  return children;
}
