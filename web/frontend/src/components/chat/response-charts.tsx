"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { BarChart3, PieChart as PieChartIcon, TrendingUp } from "lucide-react";

interface ChartData {
  type?: string;
  chart_type?: string;
  title?: string;
  data?: any[];
  stats?: any;
}

interface ResponseChartsProps {
  structuredData: ChartData | ChartData[];
}

const COLORS = {
  red: "#ef4444",
  amber: "#f59e0b",
  emerald: "#10b981",
  blue: "#3b82f6",
  purple: "#a855f7",
  zinc: "#71717a",
};

function ChartRenderer({ structuredData }: { structuredData: ChartData }) {
  if (!structuredData?.data || structuredData.data.length === 0) {
    return null;
  }

  const chartType = structuredData.chart_type || structuredData.type;
  const data = structuredData.data;

  // Bar Chart (채널 통계, 참여율 분석 등)
  if (chartType === "bar" || chartType === "channel_stats" || chartType === "engagement") {
    // 데이터 형식 변환 - 다양한 필드명 지원
    const chartData = data.map((item: any, index: number) => {
      // 라벨 추출 (한글 필드명 우선)
      const label =
        item.제목?.substring(0, 12) ||
        item.title?.substring(0, 12) ||
        item.채널?.substring(0, 12) ||
        item.channel?.substring(0, 12) ||
        item.카테고리 ||
        item.category ||
        item.range ||
        item.type ||
        item.name?.substring(0, 12) ||
        `#${item.순위 || item.rank || index + 1}`;

      // 값 추출 (한글 필드명 우선)
      const value =
        item.조회수 ||
        item.views ||
        item.subscribers ||
        item.count ||
        item.avg_views ||
        item.value ||
        0;

      return {
        name: label + (label.length >= 12 ? '...' : ''),
        value,
        label,
      };
    });

    return (
      <Card className="mt-4 bg-zinc-900/50 border-zinc-800/50">
        <CardHeader>
          <CardTitle className="text-lg text-white flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-red-400" />
            {structuredData.title || "차트"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
              <XAxis
                dataKey="name"
                tick={{ fill: "#a1a1aa", fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis tick={{ fill: "#a1a1aa", fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#27272a",
                  border: "1px solid #3f3f46",
                  borderRadius: "8px",
                  color: "#e4e4e7",
                }}
                labelStyle={{ fontWeight: 'bold', marginBottom: '4px' }}
                cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
              />
              <Legend
                wrapperStyle={{ color: "#a1a1aa", paddingTop: '20px' }}
                formatter={(value) => <span className="text-zinc-400">{value === 'value' ? '데이터' : value}</span>}
              />
              <Bar
                name={structuredData.title?.includes("구독") ? "구독자 수" : "조회수"}
                dataKey="value"
                fill={COLORS.red}
                radius={[6, 6, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    );
  }

  // Pie Chart (카테고리 통계)
  if (chartType === "pie" || chartType === "category_stats") {
    const chartData = data.map((item: any) => ({
      name: item.category || item.name || `카테고리 ${data.indexOf(item) + 1}`,
      value: item.count || item.share || item.value || 0,
    }));

    const pieColors = [COLORS.red, COLORS.amber, COLORS.emerald, COLORS.blue, COLORS.purple];

    return (
      <Card className="mt-4 bg-zinc-900/50 border-zinc-800/50">
        <CardHeader>
          <CardTitle className="text-lg text-white flex items-center gap-2">
            <PieChartIcon className="h-5 w-5 text-red-400" />
            {structuredData.title || "카테고리 분포"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={pieColors[index % pieColors.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: "#27272a",
                  border: "1px solid #3f3f46",
                  borderRadius: "8px",
                  color: "#e4e4e7",
                }}
                formatter={(value: any, name?: string) => [
                  `${value.toLocaleString()}`,
                  name === 'value' ? '수치' : (name || '데이터')
                ]}
              />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    );
  }

  // Line Chart (성장률 분석, 트렌딩 순위 등)
  if (chartType === "line" || chartType === "growth") {
    const chartData = data.map((item: any, index: number) => {
      // 다양한 필드명에서 라벨 추출 (영상 제목 우선)
      const label =
        item.제목?.substring(0, 12) ||      // 한글 필드명
        item.title?.substring(0, 12) ||      // 영어 필드명
        item.채널?.substring(0, 12) ||       // 채널명 (한글)
        item.channel?.substring(0, 12) ||    // 채널명 (영어)
        item.name?.substring(0, 12) ||       // 범용 이름
        `#${item.순위 || item.rank || index + 1}`;  // 순위 fallback

      return {
        name: label + (label.length >= 12 ? '...' : ''),
        value: item.조회수 || item.views || item.growth_rate || item.value || 0,
        views: item.조회수 || item.views || item.current_views || 0,
      };
    });

    return (
      <Card className="mt-4 bg-zinc-900/50 border-zinc-800/50">
        <CardHeader>
          <CardTitle className="text-lg text-white flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-red-400" />
            {structuredData.title || "성장률 분석"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
              <XAxis
                dataKey="name"
                tick={{ fill: "#a1a1aa", fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis tick={{ fill: "#a1a1aa", fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#27272a",
                  border: "1px solid #3f3f46",
                  borderRadius: "8px",
                  color: "#e4e4e7",
                }}
                formatter={(value: any) => [`${value.toLocaleString()}`, "조회수"]}
              />
              <Legend
                wrapperStyle={{ color: "#a1a1aa", paddingTop: '20px' }}
                formatter={(value) => <span className="text-zinc-400">{value === 'value' ? '조회수' : value}</span>}
              />
              <Line
                name="조회수"
                type="monotone"
                dataKey="value"
                stroke={COLORS.red}
                strokeWidth={3}
                dot={{ r: 6, fill: COLORS.zinc, strokeWidth: 2, stroke: COLORS.red }}
                activeDot={{ r: 8, strokeWidth: 0 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    );
  }

  // Comparison Chart (콘텐츠 유형 비교)
  if (chartType === "comparison" || chartType === "content_comparison") {
    const chartData = data.map((item: any) => ({
      name: item.type || item.name,
      조회수: item.avg_views || item.views || 0,
      참여율: item.avg_engagement || item.engagement || 0,
      동영상수: item.count || 0,
      value: item.value || 0
    }));

    // value 컬럼이 있으면 그걸 우선 그림 (단일 Bar) - 이전 로직 호환
    // 하지만 comparison은 주로 2개 이상을 비교

    return (
      <Card className="mt-4 bg-zinc-900/50 border-zinc-800/50">
        <CardHeader>
          <CardTitle className="text-lg text-white flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-red-400" />
            {structuredData.title || "비교 분석"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
              <XAxis dataKey="name" tick={{ fill: "#a1a1aa", fontSize: 12 }} />
              <YAxis tick={{ fill: "#a1a1aa", fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#27272a",
                  border: "1px solid #3f3f46",
                  borderRadius: "8px",
                  color: "#e4e4e7",
                }}
              />
              <Legend wrapperStyle={{ color: "#a1a1aa" }} />
              {/* 유연한 데이터 키 매핑 */}
              <Bar dataKey="조회수" fill={COLORS.blue} radius={[8, 8, 0, 0]} />
              <Bar dataKey="참여율" fill={COLORS.emerald} radius={[8, 8, 0, 0]} />
              {data[0]?.value && <Bar dataKey="value" fill={COLORS.red} radius={[8, 8, 0, 0]} name="값" />}
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    );
  }

  return null;
}

export function ResponseCharts({ structuredData }: ResponseChartsProps) {
  if (Array.isArray(structuredData)) {
    return (
      <div className="flex flex-col gap-4">
        {structuredData.map((data, index) => (
          <ChartRenderer key={index} structuredData={data} />
        ))}
      </div>
    );
  }

  return <ChartRenderer structuredData={structuredData} />;
}

