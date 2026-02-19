"use client";

import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import { Star } from "lucide-react";
import { getImageUrl } from "@/lib/utils";
import type { Movie } from "@/types";

interface SimilarMoviesProps {
  similar: Movie[];
}

export default function SimilarMovies({ similar }: SimilarMoviesProps) {
  if (similar.length === 0) return null;

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="overflow-hidden"
    >
      <h2 className="text-xl font-semibold text-white mb-4">비슷한 영화</h2>
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-3 md:gap-4">
        {similar.slice(0, 10).map((m) => (
          <Link key={m.id} href={`/movies/${m.id}`} className="group">
            <div className="relative aspect-[2/3] rounded-md overflow-hidden bg-dark-100">
              {m.poster_path ? (
                <Image
                  src={getImageUrl(m.poster_path, "w342")}
                  alt={m.title_ko || m.title}
                  fill
                  className="object-cover transition-transform duration-300 group-hover:scale-105"
                  sizes="(max-width: 640px) 30vw, (max-width: 768px) 22vw, 18vw"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <span className="text-3xl">🎬</span>
                </div>
              )}
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <div className="flex items-center gap-1 text-yellow-400">
                  <Star className="w-4 h-4 fill-current" />
                  <span className="text-sm font-medium">{m.vote_average.toFixed(1)}</span>
                </div>
              </div>
            </div>
            <div className="mt-1.5 text-center">
              <p className="text-sm font-medium text-white group-hover:text-primary-400 transition truncate">
                {m.title_ko || m.title}
              </p>
              {m.genres.length > 0 && (
                <p className="text-xs text-white/50 mt-0.5 truncate">
                  {m.genres.slice(0, 2).join(" · ")}
                </p>
              )}
            </div>
          </Link>
        ))}
      </div>
    </motion.section>
  );
}
