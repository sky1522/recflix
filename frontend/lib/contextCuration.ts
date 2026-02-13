// ===== 컨텍스트 타입 정의 =====
export type TimeOfDay = 'morning' | 'afternoon' | 'evening' | 'night';
export type Season = 'spring' | 'summer' | 'autumn' | 'winter';
export type TempRange = 'freezing' | 'cold' | 'cool' | 'mild' | 'warm' | 'hot';

export interface UserContext {
  timeOfDay: TimeOfDay;
  season: Season;
  tempRange: TempRange;
  tempCelsius: number;
  weatherCondition: string;
}

// ===== 감지 함수 =====
export function detectTimeOfDay(): TimeOfDay {
  const hour = new Date().getHours();
  if (hour >= 6 && hour < 12) return 'morning';
  if (hour >= 12 && hour < 18) return 'afternoon';
  if (hour >= 18 && hour < 22) return 'evening';
  return 'night';
}

export function detectSeason(): Season {
  const month = new Date().getMonth() + 1;
  if (month >= 3 && month <= 5) return 'spring';
  if (month >= 6 && month <= 8) return 'summer';
  if (month >= 9 && month <= 11) return 'autumn';
  return 'winter';
}

export function detectTempRange(celsius: number): TempRange {
  if (celsius <= -5) return 'freezing';
  if (celsius <= 5) return 'cold';
  if (celsius <= 15) return 'cool';
  if (celsius <= 22) return 'mild';
  if (celsius <= 30) return 'warm';
  return 'hot';
}

export function buildUserContext(
  tempCelsius: number,
  weatherCondition: string
): UserContext {
  return {
    timeOfDay: detectTimeOfDay(),
    season: detectSeason(),
    tempRange: detectTempRange(tempCelsius),
    tempCelsius,
    weatherCondition,
  };
}
