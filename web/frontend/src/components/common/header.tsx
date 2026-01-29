"use client";

import { Bell, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function Header() {
  return (
    <header className="h-16 border-b border-zinc-800/30 bg-zinc-950/80 backdrop-blur-xl flex items-center justify-between px-8">
      <div className="flex items-center gap-4">
        <div>
          <h2 className="text-base font-semibold text-white">YouTube Analytics AI</h2>
          <p className="text-xs text-zinc-500">실시간 데이터 분석</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9 text-zinc-400 hover:text-white hover:bg-zinc-800/50"
          aria-label="새로고침"
        >
          <RefreshCw className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9 text-zinc-400 hover:text-white hover:bg-zinc-800/50 relative"
          aria-label="알림"
        >
          <Bell className="h-4 w-4" />
          <Badge className="absolute -top-1 -right-1 h-4 w-4 p-0 flex items-center justify-center bg-red-500 text-white text-[10px] border-2 border-zinc-950">
            3
          </Badge>
        </Button>
      </div>
    </header>
  );
}
