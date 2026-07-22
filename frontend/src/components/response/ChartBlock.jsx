import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

  return (
    <div className="custom-tooltip">
      <div style={{ fontWeight: 600, marginBottom: 4 }}>
        {label}
      </div>

      <div style={{ color: "#7C3AED" }}>
        {typeof payload[0].value === "number"
          ? payload[0].value.toLocaleString()
          : payload[0].value}
      </div>
    </div>
  );
}

export default function ChartBlock({
  chart,
  rows,
}) {  if (!chart || !Array.isArray(rows) || rows.length === 0) {
  return null;
}

  const data = rows.map((row) => ({
  name: row.label,
  value: row.value,
}));

  return (
    <div className="ds-chart-area">
      <div className="ds-chart-meta">
        <div className="ds-chart-title">
          {chart?.y_label}
        </div>

        <div className="ds-chart-sub">
          by {chart?.x_label}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        {chart.chart_type === "line" ? (
          <AreaChart data={data}>
            <defs>
              <linearGradient
                id="colorVal"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="5%"
                  stopColor="#7C3AED"
                  stopOpacity={0.15}
                />
                <stop
                  offset="95%"
                  stopColor="#7C3AED"
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>

            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#F0EEFF"
            />

            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: "#9CA3AF" }}
            />

            <YAxis
              tick={{ fontSize: 11, fill: "#9CA3AF" }}
            />

            <Tooltip content={<CustomTooltip />} />

            <Area
              type="monotone"
              dataKey="value"
              stroke="#7C3AED"
              strokeWidth={2.5}
              fill="url(#colorVal)"
              dot={{
                fill: "#7C3AED",
                r: 4,
              }}
            />
          </AreaChart>
        ) : (
          <BarChart data={data}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#F0EEFF"
              vertical={false}
            />

            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: "#9CA3AF" }}
            />

            <YAxis
              tick={{ fontSize: 11, fill: "#9CA3AF" }}
            />

            <Tooltip content={<CustomTooltip />} />

            <Bar
              dataKey="value"
              fill="#7C3AED"
              radius={[6, 6, 0, 0]}
            />
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}