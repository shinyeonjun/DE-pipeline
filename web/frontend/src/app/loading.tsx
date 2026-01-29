export default function Loading() {
  return (
    <div className="flex items-center justify-center h-screen bg-zinc-950">
      <div className="text-center space-y-4">
        <div className="w-16 h-16 border-4 border-red-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-zinc-400 text-sm">로딩 중...</p>
      </div>
    </div>
  );
}

