import { useState, useEffect } from 'react';

/**
 * 사이드바 상태 관리 훅
 * localStorage와 동기화 (Hydration 안전)
 */
export function useSidebarState() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);

  // Hydration 후 localStorage에서 상태 로드
  useEffect(() => {
    setIsHydrated(true);
    const savedState = localStorage.getItem('sidebarCollapsed');
    if (savedState !== null) {
      setSidebarCollapsed(JSON.parse(savedState));
    }
  }, []);

  const toggleSidebar = () => {
    const newState = !sidebarCollapsed;
    setSidebarCollapsed(newState);
    localStorage.setItem('sidebarCollapsed', JSON.stringify(newState));
  };

  return { sidebarCollapsed, toggleSidebar, isHydrated };
}

