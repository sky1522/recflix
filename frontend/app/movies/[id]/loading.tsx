export default function MovieDetailLoading() {
  return (
    <div className="min-h-screen bg-surface">
      {/* Hero area */}
      <div className="relative h-[50vh] bg-zinc-800/50 animate-pulse" />

      <div className="max-w-5xl mx-auto px-4 md:px-8 -mt-32 relative z-10">
        <div className="flex flex-col md:flex-row gap-8">
          {/* Poster */}
          <div className="flex-shrink-0 w-64 md:w-80">
            <div className="aspect-[2/3] bg-zinc-800/50 rounded-lg animate-pulse" />
          </div>

          {/* Info */}
          <div className="flex-1 space-y-4 pt-4">
            <div className="h-10 w-3/4 bg-zinc-800/50 rounded animate-pulse" />
            <div className="flex gap-3">
              <div className="h-6 w-16 bg-zinc-800/50 rounded animate-pulse" />
              <div className="h-6 w-20 bg-zinc-800/50 rounded animate-pulse" />
              <div className="h-6 w-14 bg-zinc-800/50 rounded animate-pulse" />
            </div>
            <div className="flex gap-2">
              <div className="h-8 w-20 bg-zinc-800/50 rounded-full animate-pulse" />
              <div className="h-8 w-16 bg-zinc-800/50 rounded-full animate-pulse" />
              <div className="h-8 w-24 bg-zinc-800/50 rounded-full animate-pulse" />
            </div>
            <div className="space-y-2 pt-4">
              <div className="h-4 w-full bg-zinc-800/50 rounded animate-pulse" />
              <div className="h-4 w-5/6 bg-zinc-800/50 rounded animate-pulse" />
              <div className="h-4 w-4/6 bg-zinc-800/50 rounded animate-pulse" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
