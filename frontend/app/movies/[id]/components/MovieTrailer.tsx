"use client";

import { motion } from "framer-motion";

interface MovieTrailerProps {
  trailerKey: string | null | undefined;
}

export default function MovieTrailer({ trailerKey }: MovieTrailerProps) {
  if (!trailerKey) return null;

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.45 }}
    >
      <h2 className="text-xl font-semibold text-white mb-4">트레일러</h2>
      <div className="aspect-video rounded-xl overflow-hidden bg-dark-100">
        <iframe
          src={`https://www.youtube.com/embed/${trailerKey}`}
          title="트레일러"
          className="w-full h-full"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          loading="lazy"
        />
      </div>
    </motion.section>
  );
}
