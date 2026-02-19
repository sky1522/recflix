"use client";

import { useEffect, useRef } from "react";
import { trackEvent } from "@/lib/eventTracker";

/**
 * 추천 섹션 뷰포트 노출 감지 훅.
 * 30% 이상 보이면 한 번만 recommendation_impression 이벤트 전송.
 */
export function useImpressionTracker(
  section: string,
  movieIds: number[],
  enabled: boolean = true,
) {
  const ref = useRef<HTMLElement>(null);
  const tracked = useRef(false);

  useEffect(() => {
    if (!enabled || tracked.current || !ref.current || movieIds.length === 0) {
      return;
    }

    const el = ref.current;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !tracked.current) {
          tracked.current = true;
          trackEvent({
            event_type: "recommendation_impression",
            metadata: {
              section,
              movie_ids: movieIds.slice(0, 10),
              count: movieIds.length,
            },
          });
          observer.disconnect();
        }
      },
      { threshold: 0.3 },
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [section, movieIds, enabled]);

  return ref;
}
