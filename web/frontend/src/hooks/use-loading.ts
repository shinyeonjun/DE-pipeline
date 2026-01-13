import { useState, useEffect } from 'react';

/**
 * 초기 데이터 로딩 시뮬레이션 훅
 * 실제 API 연결 시 이 훅을 데이터 fetching 훅으로 대체
 */
export function useLoading(delay: number = 1000) {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, delay);

    return () => clearTimeout(timer);
  }, [delay]);

  return isLoading;
}

