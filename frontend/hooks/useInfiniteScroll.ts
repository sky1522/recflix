"use client";

import { useRef, useCallback, useEffect } from "react";

interface UseInfiniteScrollOptions {
  onLoadMore: () => void;
  hasMore: boolean;
  isLoading: boolean;
  enabled?: boolean;
  threshold?: number;
  rootMargin?: string;
}

/**
 * Infinite scroll hook using Intersection Observer with callback ref
 */
export function useInfiniteScroll({
  onLoadMore,
  hasMore,
  isLoading,
  enabled = true,
  threshold = 0.1,
  rootMargin = "200px",
}: UseInfiniteScrollOptions) {
  const observerRef = useRef<IntersectionObserver | null>(null);
  const nodeRef = useRef<HTMLDivElement | null>(null);

  // Store latest callback to avoid stale closures
  const onLoadMoreRef = useRef(onLoadMore);
  const hasMoreRef = useRef(hasMore);
  const isLoadingRef = useRef(isLoading);

  useEffect(() => {
    onLoadMoreRef.current = onLoadMore;
    hasMoreRef.current = hasMore;
    isLoadingRef.current = isLoading;
  }, [onLoadMore, hasMore, isLoading]);

  // Callback ref that properly handles element attachment/detachment
  const loadMoreRef = useCallback(
    (node: HTMLDivElement | null) => {
      // Clean up previous observer
      if (observerRef.current) {
        observerRef.current.disconnect();
        observerRef.current = null;
      }

      nodeRef.current = node;

      // Don't observe if not enabled or no node
      if (!enabled || !node) return;

      observerRef.current = new IntersectionObserver(
        (entries) => {
          const [entry] = entries;
          if (entry.isIntersecting && hasMoreRef.current && !isLoadingRef.current) {
            onLoadMoreRef.current();
          }
        },
        { threshold, rootMargin }
      );

      observerRef.current.observe(node);
    },
    [enabled, threshold, rootMargin]
  );

  // Re-observe when enabled changes
  useEffect(() => {
    if (!enabled && observerRef.current) {
      observerRef.current.disconnect();
      observerRef.current = null;
    } else if (enabled && nodeRef.current && !observerRef.current) {
      observerRef.current = new IntersectionObserver(
        (entries) => {
          const [entry] = entries;
          if (entry.isIntersecting && hasMoreRef.current && !isLoadingRef.current) {
            onLoadMoreRef.current();
          }
        },
        { threshold, rootMargin }
      );
      observerRef.current.observe(nodeRef.current);
    }
  }, [enabled, threshold, rootMargin]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, []);

  return { loadMoreRef };
}
