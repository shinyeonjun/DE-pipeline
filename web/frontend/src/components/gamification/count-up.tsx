"use client";

import { useCountUp, useInView } from "@/lib/animations";
import { formatNumber } from "@/lib/formatters";

interface CountUpProps {
  end: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
  format?: boolean;
  className?: string;
}

export function CountUp({
  end,
  duration = 1500,
  prefix = "",
  suffix = "",
  format = true,
  className = "",
}: CountUpProps) {
  const { ref, hasBeenInView } = useInView({ threshold: 0.1 });
  const count = useCountUp(hasBeenInView ? end : 0, duration);

  return (
    <span ref={ref} className={className}>
      {prefix}
      {format ? formatNumber(count) : count}
      {suffix}
    </span>
  );
}

