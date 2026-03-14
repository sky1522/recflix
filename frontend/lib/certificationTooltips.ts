export const CERTIFICATION_TOOLTIPS: Record<string, { label: string; description: string }> = {
  "G":     { label: "전체 관람가", description: "모든 연령층 관람 가능, 유해 요소 없음" },
  "PG":    { label: "12세 관람가", description: "부모 지도가 필요하거나 13세 미만 주의 콘텐츠" },
  "PG-13": { label: "12~15세 관람가", description: "부모 지도가 필요하거나 13세 미만 주의 콘텐츠" },
  "R":     { label: "15세~19세 관람가", description: "폭력성, 언어 수위 등으로 성인 보호자 동반 필요" },
  "NC-17": { label: "청소년 관람불가", description: "19세 미만 관람 절대 불가, 성인 전용 콘텐츠" },
  "NR":    { label: "19+ (미정)", description: "등급 미정 데이터는 보수적으로 성인물로 우선 분류" },
  "UR":    { label: "19+ (미정)", description: "등급 미정 데이터는 보수적으로 성인물로 우선 분류" },
  "12":    { label: "12세 이상 관람가", description: "12세 미만은 보호자 동반 시 관람 가능" },
  "15":    { label: "15세 이상 관람가", description: "15세 미만 관람 불가" },
  "18":    { label: "청소년 관람불가", description: "18세 미만 관람 불가, 성인 전용" },
  "19":    { label: "청소년 관람불가", description: "19세 미만 관람 불가, 성인 전용" },
  "ALL":   { label: "전체 관람가", description: "모든 연령층 관람 가능" },
};

export const DEFAULT_TOOLTIP = { label: "등급 정보", description: "상세 등급 정보를 확인해주세요" };
