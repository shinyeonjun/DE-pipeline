"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  TrendingUp,
  Users,
  FolderOpen,
  MessageSquare,
  Youtube,
  Flame,
  BarChart3,
} from "lucide-react";

const navigation = [
  { name: "AI 분석", href: "/", icon: MessageSquare },
  { name: "트렌딩", href: "/trending", icon: TrendingUp },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-20 flex-col bg-zinc-950 border-r border-zinc-800/30">
      {/* Logo */}
      <div className="flex h-16 items-center justify-center border-b border-zinc-800/30">
        <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-red-600 rounded-xl flex items-center justify-center shadow-lg shadow-red-500/20">
          <Youtube className="h-6 w-6 text-white" />
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-8 space-y-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group relative flex flex-col items-center justify-center h-14 rounded-xl transition-all",
                isActive
                  ? "bg-red-500/10 text-white"
                  : "text-zinc-500 hover:bg-zinc-800/50 hover:text-white"
              )}
              title={item.name}
            >
              <item.icon
                className={cn(
                  "h-6 w-6 mb-1 transition-transform group-hover:scale-110",
                  isActive && "text-red-500"
                )}
              />
              <span className={cn(
                "text-[10px] font-medium",
                isActive ? "text-white" : "text-zinc-600"
              )}>{item.name.split(' ')[0]}</span>
              
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-red-500 rounded-r-full" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Status */}
      <div className="px-3 pb-4">
        <div className="flex items-center justify-center w-14 h-14 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
          <div className="relative">
            <div className="w-2 h-2 bg-green-500 rounded-full" />
            <div className="absolute inset-0 w-2 h-2 bg-green-500 rounded-full animate-ping" />
          </div>
        </div>
      </div>
    </div>
  );
}
