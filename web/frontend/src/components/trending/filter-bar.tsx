"use client";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Filter, ArrowUpDown } from "lucide-react";
import { CATEGORY_MAP } from "@/lib/constants";

interface FilterBarProps {
  onCategoryChange?: (category: string) => void;
  onTypeChange?: (type: string) => void;
  onSortChange?: (sort: string) => void;
}

export function FilterBar({ onCategoryChange, onTypeChange, onSortChange }: FilterBarProps) {
  return (
    <div className="flex items-center gap-4 mb-6">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="bg-zinc-900 border-zinc-700 text-white">
            <Filter className="h-4 w-4 mr-2" />
            카테고리
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="bg-zinc-900 border-zinc-700">
          <DropdownMenuItem onClick={() => onCategoryChange?.("all")}>전체</DropdownMenuItem>
          <DropdownMenuItem onClick={() => onCategoryChange?.("Music")}>{CATEGORY_MAP.Music}</DropdownMenuItem>
          <DropdownMenuItem onClick={() => onCategoryChange?.("Entertainment")}>{CATEGORY_MAP.Entertainment}</DropdownMenuItem>
          <DropdownMenuItem onClick={() => onCategoryChange?.("Gaming")}>{CATEGORY_MAP.Gaming}</DropdownMenuItem>
          <DropdownMenuItem onClick={() => onCategoryChange?.("News")}>{CATEGORY_MAP.News}</DropdownMenuItem>
          <DropdownMenuItem onClick={() => onCategoryChange?.("Sports")}>{CATEGORY_MAP.Sports}</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="bg-zinc-900 border-zinc-700 text-white">
            <Filter className="h-4 w-4 mr-2" />
            콘텐츠 타입
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="bg-zinc-900 border-zinc-700">
          <DropdownMenuItem onClick={() => onTypeChange?.("all")}>전체</DropdownMenuItem>
          <DropdownMenuItem onClick={() => onTypeChange?.("normal")}>일반 영상</DropdownMenuItem>
          <DropdownMenuItem onClick={() => onTypeChange?.("shorts")}>쇼츠</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="bg-zinc-900 border-zinc-700 text-white">
            <ArrowUpDown className="h-4 w-4 mr-2" />
            정렬
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="bg-zinc-900 border-zinc-700">
          <DropdownMenuItem onClick={() => onSortChange?.("rank")}>순위순</DropdownMenuItem>
          <DropdownMenuItem onClick={() => onSortChange?.("views")}>조회수순</DropdownMenuItem>
          <DropdownMenuItem onClick={() => onSortChange?.("likes")}>좋아요순</DropdownMenuItem>
          <DropdownMenuItem onClick={() => onSortChange?.("engagement")}>참여율순</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
