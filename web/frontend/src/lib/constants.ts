/**
 * 카테고리 한영 매핑
 */
export const CATEGORY_MAP: Record<string, string> = {
  Music: "음악",
  Entertainment: "엔터테인먼트",
  Gaming: "게임",
  News: "뉴스",
  "News & Politics": "뉴스·정치",
  Sports: "스포츠",
  Education: "교육",
  "Howto & Style": "하우투·스타일",
  "People & Blogs": "인물·블로그",
  Others: "기타",
};

/**
 * 카테고리 영문명을 한국어로 변환
 */
export function getCategoryName(category: string): string {
  return CATEGORY_MAP[category] || category;
}

/**
 * 한국어 카테고리명을 영문명으로 변환 (API 호출용)
 */
export function getCategoryKey(koreanName: string): string {
  const entries = Object.entries(CATEGORY_MAP);
  const found = entries.find(([_, ko]) => ko === koreanName);
  return found ? found[0] : koreanName;
}

