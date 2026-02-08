import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";

export default function GoalDonut({ data }) {
// NOTE: not specifying colors manually per your UI can be done,
// but Recharts will default; we’ll keep it minimal and still readable.
const palette = ["#64748b", "#3b82f6", "#a855f7", "#10b981"]; // subtle, matches dark UI vibe

    return (
        <div className="card">
            <div className="card-title-row">
            <div className="card-title">Goal for Today</div>
            <div className="card-subtitle">AI tracks daily plan + carryover</div>
            </div>

            <div className="chart-wrap">
            <div className="legend-left">
                {data.map((d) => (
                <div key={d.name} className="legend-row">
                    <span className="legend-dot" />
                    <span className="legend-text">
                    {d.name}: {d.value} ({d.pct}%)
                    </span>
                </div>
                ))}
                <div className="hint">
                Tip: unfinished goals roll into tomorrow (cumulative).
                </div>
            </div>

            <div className="donut-right">
                <ResponsiveContainer width="100%" height={280}>
                <PieChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                    <Pie
                    data={data}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={72}
                    outerRadius={110}
                    paddingAngle={2}
                    stroke="rgba(15,23,42,1)"   // helps define edge on dark bg
                    strokeWidth={2}
                    isAnimationActive={false}
                    >
                    {data.map((_, idx) => (
                        <Cell key={idx} fill={palette[idx % palette.length]} />
                    ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                </PieChart>
                </ResponsiveContainer>
            </div>
            </div>
        </div>
    );
}
