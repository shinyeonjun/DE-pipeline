"use client";

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";

interface CategoryData {
  name: string;
  value: number;
  color: string;
  [key: string]: string | number;
}

interface CategoryChartProps {
  data: CategoryData[];
}

export function CategoryChart({ data }: CategoryChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: "#27272a",
            border: "1px solid #3f3f46",
            borderRadius: "8px",
            padding: "8px 12px",
            boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.3)",
          }}
          labelStyle={{ color: "#fff", fontWeight: 600, marginBottom: "4px" }}
          itemStyle={{ color: "#e4e4e7" }}
          cursor={{ fill: "rgba(255, 255, 255, 0.1)" }}
        />
        <Legend
          wrapperStyle={{ color: "#a1a1aa" }}
          formatter={(value) => <span style={{ color: "#a1a1aa" }}>{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
