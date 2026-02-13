import type { Metadata, Viewport } from "next";
import "./globals.css";
import Header from "@/components/layout/Header";
import MobileNav from "@/components/layout/MobileNav";

export const metadata: Metadata = {
  metadataBase: new URL("https://jnsquery-reflix.vercel.app"),
  title: "RecFlix - Personalized Movie Recommendations",
  description: "MBTI, 날씨, 기분 기반 맞춤형 영화 추천 서비스",
  manifest: "/manifest.json",
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon.svg", type: "image/svg+xml" },
    ],
  },
  openGraph: {
    siteName: "RecFlix",
    type: "website",
    locale: "ko_KR",
    url: "https://jnsquery-reflix.vercel.app",
    title: "RecFlix - 맞춤형 영화 추천",
    description: "MBTI, 날씨, 기분 기반 맞춤형 영화 추천 서비스",
    images: [
      {
        url: "https://jnsquery-reflix.vercel.app/favicon.svg",
        width: 512,
        height: 512,
        alt: "RecFlix",
      },
    ],
  },
  twitter: {
    card: "summary",
    title: "RecFlix - 맞춤형 영화 추천",
    description: "MBTI, 날씨, 기분 기반 맞춤형 영화 추천 서비스",
  },
  other: {
    "mobile-web-app-capable": "yes",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-dark-200">
        <Header />
        <main className="pt-14 md:pt-16 pb-16 md:pb-0">{children}</main>
        <MobileNav />
      </body>
    </html>
  );
}
