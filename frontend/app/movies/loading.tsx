export default function MoviesLoading() {
  return (
    <div className="min-h-screen bg-dark-200 pt-20 pb-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Title */}
        <div className="mb-8">
          <div className="h-10 w-48 bg-zinc-800/50 rounded animate-pulse mb-6" />
          {/* Search bar */}
          <div className="h-12 w-full bg-zinc-800/50 rounded-lg animate-pulse mb-6" />
          {/* Filter bar */}
          <div className="flex gap-4">
            <div className="h-10 w-32 bg-zinc-800/50 rounded-lg animate-pulse" />
            <div className="h-10 w-32 bg-zinc-800/50 rounded-lg animate-pulse" />
            <div className="h-10 w-28 bg-zinc-800/50 rounded-lg animate-pulse" />
          </div>
        </div>

        {/* Movie grid skeleton (4x6) */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {Array.from({ length: 24 }, (_, i) => (
            <div key={i}>
              <div className="aspect-[2/3] bg-zinc-800/50 rounded-md animate-pulse" />
              <div className="mt-2 space-y-1.5 px-1">
                <div className="h-4 bg-zinc-800/50 rounded animate-pulse" />
                <div className="h-3 w-2/3 bg-zinc-800/50 rounded animate-pulse mx-auto" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
