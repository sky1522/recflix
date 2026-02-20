/** 자연어 쿼리인지 판별 (간단 휴리스틱) */
export function isNaturalLanguageQuery(query: string): boolean {
  const words = query.trim().split(/\s+/);
  if (words.length <= 2) return false;

  const nlPatterns = [
    /좋은|어울리는|볼만한|추천|찾아/,
    /기분|분위기|느낌|감성|무드/,
    /날씨|비|눈|맑은|흐린|추운|더운/,
    /혼자|같이|연인|가족|친구|데이트/,
    /잔잔한|긴장감|무서운|재밌는|슬픈|감동|웃긴|따뜻한|시원한/,
    /싶|때|날|영화|보기/,
  ];

  return nlPatterns.some((p) => p.test(query));
}
