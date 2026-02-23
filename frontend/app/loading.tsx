export default function HomeLoading() {
  return (
    <div className="min-h-screen bg-dark-200">
      {/* Banner skeleton */}
      <div className="relative h-[60vh] bg-zinc-800/50 animate-pulse rounded-b-lg" />

      {/* Movie rows skeleton (3 rows) */}
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-8 space-y-10">
        {[1, 2, 3].map((row) => (
          <div key={row}>
            <div className="h-7 w-48 bg-zinc-800/50 rounded animate-pulse mb-4" />
            <div className="flex space-x-3 overflow-hidden">
              {Array.from({ length: 6 }, (_, i) => (
                <div key={i} className="flex-shrink-0 w-[160px] md:w-[200px]">
                  <div className="aspect-[2/3] bg-zinc-800/50 rounded-md animate-pulse" />
                  <div className="mt-2 space-y-1.5 px-1">
                    <div className="h-4 bg-zinc-800/50 rounded animate-pulse" />
                    <div className="h-3 w-2/3 bg-zinc-800/50 rounded animate-pulse mx-auto" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
