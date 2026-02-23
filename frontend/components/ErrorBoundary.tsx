"use client";

import React from "react";
import Link from "next/link";

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

export default class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo): void {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <div className="flex items-center justify-center min-h-screen bg-dark-200 px-4">
        <div className="text-center max-w-md">
          <h2 className="text-2xl font-bold text-white mb-3">
            문제가 발생했습니다
          </h2>
          <p className="text-zinc-400 mb-6">
            예상치 못한 오류가 발생했습니다. 페이지를 새로고침하거나 홈으로
            이동해주세요.
          </p>
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={() => window.location.reload()}
              className="px-5 py-2.5 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition"
            >
              새로고침
            </button>
            <Link
              href="/"
              className="px-5 py-2.5 bg-zinc-700 hover:bg-zinc-600 text-white font-medium rounded-lg transition"
            >
              홈으로
            </Link>
          </div>
        </div>
      </div>
    );
  }
}
