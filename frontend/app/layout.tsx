import type { Metadata, Viewport } from "next";
import "./globals.css";
import Header from "@/components/layout/Header";
import MobileNav from "@/components/layout/MobileNav";

export const metadata: Metadata = {
  title: "RecFlix - Personalized Movie Recommendations",
  description: "Context-aware personalized movie recommendation platform",
  manifest: "/manifest.json",
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon.svg", type: "image/svg+xml" },
    ],
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
