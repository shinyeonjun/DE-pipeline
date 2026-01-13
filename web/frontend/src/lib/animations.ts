import { useEffect, useState, useRef } from "react";

/**
 * 숫자 카운트업 애니메이션 훅
 */
export function useCountUp(
  end: number,
  duration: number = 1500,
  start: number = 0
): number {
  const [count, setCount] = useState(start);
  const countRef = useRef(start);
  const startTimeRef = useRef<number | null>(null);

  useEffect(() => {
    const animate = (timestamp: number) => {
      if (!startTimeRef.current) {
        startTimeRef.current = timestamp;
      }

      const progress = Math.min((timestamp - startTimeRef.current) / duration, 1);
      
      // Easing function (ease-out-cubic)
      const easedProgress = 1 - Math.pow(1 - progress, 3);
      
      const currentCount = Math.floor(start + (end - start) * easedProgress);
      
      if (countRef.current !== currentCount) {
        countRef.current = currentCount;
        setCount(currentCount);
      }

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setCount(end);
      }
    };

    requestAnimationFrame(animate);
  }, [end, duration, start]);

  return count;
}

/**
 * 요소가 뷰포트에 들어올 때 애니메이션 트리거
 */
export function useInView(options?: IntersectionObserverInit) {
  const [isInView, setIsInView] = useState(false);
  const [hasBeenInView, setHasBeenInView] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      setIsInView(entry.isIntersecting);
      if (entry.isIntersecting && !hasBeenInView) {
        setHasBeenInView(true);
      }
    }, options);

    const currentRef = ref.current;
    if (currentRef) {
      observer.observe(currentRef);
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
    };
  }, [hasBeenInView, options]);

  return { ref, isInView, hasBeenInView };
}

/**
 * 순차적 지연 애니메이션을 위한 지연 계산
 */
export function getStaggerDelay(index: number, baseDelay: number = 50): number {
  return index * baseDelay;
}

/**
 * 랭킹 변화 애니메이션 클래스
 */
export function getRankChangeAnimation(change: number): string {
  if (change > 0) return "animate-bounce-up";
  if (change < 0) return "animate-bounce-down";
  return "";
}

/**
 * 레벨 계산 (조회수 기반)
 */
export function calculateLevel(viewCount: number): {
  level: number;
  progress: number;
  nextLevelViews: number;
} {
  // 레벨 공식: 레벨 = floor(log10(조회수) * 2)
  const level = Math.max(1, Math.floor(Math.log10(Math.max(viewCount, 1)) * 2));
  const currentLevelViews = Math.pow(10, level / 2);
  const nextLevelViews = Math.pow(10, (level + 1) / 2);
  const progress = ((viewCount - currentLevelViews) / (nextLevelViews - currentLevelViews)) * 100;

  return {
    level,
    progress: Math.min(100, Math.max(0, progress)),
    nextLevelViews: Math.floor(nextLevelViews),
  };
}

/**
 * 배지 획득 조건 확인
 */
export interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  condition: (video: {
    viewCount: number;
    likeCount: number;
    commentCount: number;
    engagementRate: string;
    hoursAgo: number;
  }) => boolean;
}

export const badges: Badge[] = [
  {
    id: "viral",
    name: "바이럴 킹",
    description: "조회수 1천만 돌파",
    icon: "🔥",
    color: "from-red-500 to-orange-500",
    condition: (video) => video.viewCount >= 10000000,
  },
  {
    id: "mega-hit",
    name: "메가 히트",
    description: "조회수 5백만 돌파",
    icon: "💥",
    color: "from-purple-500 to-pink-500",
    condition: (video) => video.viewCount >= 5000000,
  },
  {
    id: "super-engaging",
    name: "초참여 영상",
    description: "참여율 8% 이상",
    icon: "⚡",
    color: "from-yellow-500 to-amber-500",
    condition: (video) => Number(video.engagementRate) >= 8,
  },
  {
    id: "comment-magnet",
    name: "댓글 자석",
    description: "댓글 5만개 이상",
    icon: "💬",
    color: "from-blue-500 to-cyan-500",
    condition: (video) => video.commentCount >= 50000,
  },
  {
    id: "fresh-hit",
    name: "신선 폭발",
    description: "24시간 내 인기 영상",
    icon: "🌟",
    color: "from-green-500 to-emerald-500",
    condition: (video) => video.hoursAgo <= 24 && video.viewCount >= 1000000,
  },
  {
    id: "like-master",
    name: "좋아요 마스터",
    description: "좋아요 50만 이상",
    icon: "👍",
    color: "from-pink-500 to-rose-500",
    condition: (video) => video.likeCount >= 500000,
  },
];

export function getEarnedBadges(video: {
  viewCount: number;
  likeCount: number;
  commentCount: number;
  engagementRate: string;
  hoursAgo: number;
}): Badge[] {
  return badges.filter((badge) => badge.condition(video));
}

