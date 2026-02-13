"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function MovieError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Movie detail error:", error);
  }, [error]);

  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center px-4 text-center">
      <div className="w-16 h-16 rounded-full bg-primary-600/20 flex items-center justify-center mb-6">
        <svg
          className="w-8 h-8 text-primary-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"
          />
        </svg>
      </div>
      <h1 className="text-2xl font-bold text-white mb-2">
        영화를 찾을 수 없습니다
      </h1>
      <p className="text-gray-400 mb-8 max-w-md">
        요청하신 영화 정보를 불러올 수 없습니다. 삭제되었거나 잘못된 주소일 수
        있습니다.
      </p>
      <div className="flex gap-3">
        <button
          onClick={reset}
          className="px-6 py-3 bg-dark-100 hover:bg-zinc-800 text-white font-medium rounded-lg transition-colors border border-zinc-700"
        >
          다시 시도
        </button>
        <Link
          href="/"
          className="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors"
        >
          홈으로 돌아가기
        </Link>
      </div>
    </div>
  );
}
