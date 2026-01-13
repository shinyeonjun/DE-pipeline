/**
 * 숫자를 한국식으로 포맷팅 (만, 억 단위)
 * @param num 포맷팅할 숫자
 * @returns 포맷팅된 문자열 (예: "150만", "1.2억", "5,000")
 */
export function formatNumber(num: number): string {
  if (num >= 100000000) {
    // 1억 이상
    return (num / 100000000).toFixed(1).replace(/\.0$/, "") + "억";
  }
  if (num >= 10000) {
    // 1만 이상
    return (num / 10000).toFixed(1).replace(/\.0$/, "") + "만";
  }
  if (num >= 1000) {
    // 1천 이상
    return num.toLocaleString("ko-KR");
  }
  return num.toString();
}

/**
 * 숫자를 전체 형식으로 포맷팅 (쉼표 구분)
 * @param num 포맷팅할 숫자
 * @returns 포맷팅된 문자열 (예: "1,234,567")
 */
export function formatFullNumber(num: number): string {
  return num.toLocaleString("ko-KR");
}

/**
 * 참여율(Engagement Rate)을 색상 클래스로 변환
 * @param rate 참여율 (숫자 또는 문자열)
 * @returns Tailwind CSS 클래스명
 */
export function getEngagementColorClass(rate: number | string): string {
  const numRate = typeof rate === "string" ? parseFloat(rate) : rate;

  if (numRate > 5) {
    return "bg-green-500/20 text-green-400 border-green-500/30";
  }
  if (numRate > 3) {
    return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
  }
  return "bg-zinc-500/20 text-zinc-400 border-zinc-500/30";
}

/**
 * 순위 변동을 표시 문자열로 변환
 * @param change 순위 변동 (양수: 상승, 음수: 하락, 0: 유지)
 * @returns 표시 문자열 (예: "▲5", "▼3", "-")
 */
export function formatRankChange(change: number): string {
  if (change > 0) return `▲${change}`;
  if (change < 0) return `▼${Math.abs(change)}`;
  return "-";
}

/**
 * 순위 변동 색상 클래스
 */
export function getRankChangeColorClass(change: number): string {
  if (change > 0) return "text-green-400";
  if (change < 0) return "text-red-400";
  return "text-zinc-500";
}

/**
 * 시간 경과를 한국어로 표시
 * @param hours 경과 시간
 * @returns 표시 문자열 (예: "3시간 전", "2일 전")
 */
export function formatTimeAgo(hours: number): string {
  if (hours < 1) {
    return "방금 전";
  }
  if (hours < 24) {
    return `${Math.floor(hours)}시간 전`;
  }
  if (hours < 24 * 7) {
    return `${Math.floor(hours / 24)}일 전`;
  }
  return `${Math.floor(hours / 24 / 7)}주 전`;
}

/**
 * 영상 길이를 분:초 형식으로 변환
 * @param seconds 초 단위 길이
 * @returns 표시 문자열 (예: "3:45", "1:02:30")
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

/**
 * 퍼센트 변화량 포맷팅
 * @param value 변화량
 * @returns 표시 문자열 (예: "+12.5%", "-3.2%")
 */
export function formatPercentChange(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}
