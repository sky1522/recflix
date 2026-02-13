import type { Metadata } from "next";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const SITE_URL = "https://jnsquery-reflix.vercel.app";

interface MovieMeta {
  title: string;
  title_ko: string | null;
  overview: string | null;
  poster_path: string | null;
}

async function fetchMovie(id: string): Promise<MovieMeta | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/movies/${id}`, {
      next: { revalidate: 86400 },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: { id: string };
}): Promise<Metadata> {
  const movie = await fetchMovie(params.id);

  if (!movie) {
    return { title: "RecFlix" };
  }

  const title = movie.title_ko || movie.title;
  const description = movie.overview
    ? movie.overview.length > 160
      ? movie.overview.slice(0, 157) + "..."
      : movie.overview
    : `${title} - RecFlix에서 확인하세요`;
  const imageUrl = movie.poster_path
    ? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
    : `${SITE_URL}/og-default.png`;
  const pageUrl = `${SITE_URL}/movies/${params.id}`;

  return {
    title: `${title} | RecFlix`,
    description,
    openGraph: {
      title,
      description,
      url: pageUrl,
      siteName: "RecFlix",
      type: "video.movie",
      images: [
        {
          url: imageUrl,
          width: 500,
          height: 750,
          alt: title,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [imageUrl],
    },
  };
}

export default function MovieLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
