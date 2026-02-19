/**
 * Event Tracker - 사용자 행동 이벤트 배치 전송
 *
 * 핵심 설계:
 * 1. 배치 전송: 이벤트를 모아서 5초마다 한 번에 전송
 * 2. 실패 무시: 전송 실패가 UX에 영향 주지 않음
 * 3. 페이지 이탈 시 전송: Beacon API 사용
 * 4. SSR 안전: 서버에서는 null 싱글톤
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

type EventType =
  | "movie_click"
  | "movie_detail_view"
  | "movie_detail_leave"
  | "recommendation_impression"
  | "search"
  | "search_click"
  | "rating"
  | "favorite_add"
  | "favorite_remove";

export interface TrackEvent {
  event_type: EventType;
  movie_id?: number;
  metadata?: Record<string, unknown>;
}

interface EventPayload {
  event_type: string;
  movie_id?: number;
  session_id: string;
  metadata?: Record<string, unknown>;
}

class EventTracker {
  private queue: EventPayload[] = [];
  private flushTimer: ReturnType<typeof setInterval> | null = null;
  private sessionId: string;

  constructor() {
    this.sessionId = this.getOrCreateSessionId();
    this.startAutoFlush();
    this.setupBeforeUnload();
  }

  track(event: TrackEvent): void {
    this.queue.push({
      event_type: event.event_type,
      movie_id: event.movie_id,
      session_id: this.sessionId,
      metadata: event.metadata,
    });
  }

  private async flush(): Promise<void> {
    if (this.queue.length === 0) return;

    const events = [...this.queue];
    this.queue = [];

    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      const token = localStorage.getItem("access_token");
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      await fetch(`${API_BASE_URL}/events/batch`, {
        method: "POST",
        headers,
        body: JSON.stringify({ events }),
      });
    } catch {
      console.warn("[EventTracker] flush failed");
    }
  }

  private startAutoFlush(): void {
    this.flushTimer = setInterval(() => this.flush(), 5000);
  }

  private setupBeforeUnload(): void {
    window.addEventListener("beforeunload", () => {
      if (this.queue.length > 0) {
        const blob = new Blob([JSON.stringify({ events: this.queue })], {
          type: "application/json",
        });
        navigator.sendBeacon(`${API_BASE_URL}/events/batch`, blob);
        this.queue = [];
      }
    });
  }

  private getOrCreateSessionId(): string {
    const key = "recflix_session_id";
    let id = sessionStorage.getItem(key);
    if (!id) {
      id = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
      sessionStorage.setItem(key, id);
    }
    return id;
  }
}

// 싱글톤: 클라이언트에서만 생성
const tracker =
  typeof window !== "undefined" ? new EventTracker() : null;

/** 이벤트 추적 편의 함수. SSR에서는 no-op. */
export function trackEvent(event: TrackEvent): void {
  tracker?.track(event);
}
