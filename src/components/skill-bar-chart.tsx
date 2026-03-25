import {
	Bar,
	BarChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import { useSkillDemand } from "../hooks/use-job-data";
import type { FilterState } from "../types";

interface SkillBarChartProps {
	filters: FilterState;
}

interface TooltipPayloadEntry {
	payload: { skill_norm: string; count: number; pct_of_postings: number };
}

function CustomTooltip({
	active,
	payload,
}: {
	active?: boolean;
	payload?: TooltipPayloadEntry[];
}) {
	if (!active || !payload || payload.length === 0) return null;
	const data = payload[0].payload;
	return (
		<div
			style={{
				backgroundColor: "#1a1a2e",
				border: "1px solid #333",
				borderRadius: "6px",
				padding: "10px 14px",
				color: "#e0e0e0",
				fontSize: "0.85rem",
			}}
		>
			<div style={{ fontWeight: 700, marginBottom: "4px" }}>
				{data.skill_norm}
			</div>
			<div>Count: {data.count}</div>
			<div>{(data.pct_of_postings * 100).toFixed(1)}% of postings</div>
		</div>
	);
}

function SkillBarChart({ filters }: SkillBarChartProps) {
	const { data, isLoading } = useSkillDemand(filters);

	if (isLoading) {
		return (
			<div style={{ color: "#888", padding: "2rem", textAlign: "center" }}>
				Loading skills...
			</div>
		);
	}

	if (!data || data.length === 0) {
		return (
			<div style={{ color: "#555", padding: "4rem", textAlign: "center" }}>
				<p style={{ fontSize: "1.1rem", margin: "0 0 8px" }}>No data yet</p>
				<p style={{ fontSize: "0.85rem", margin: 0 }}>
					Click &ldquo;Sync Now&rdquo; to fetch job postings
				</p>
			</div>
		);
	}

	const sorted = [...data].sort((a, b) => a.count - b.count).slice(-20);
	const chartHeight = Math.max(400, sorted.length * 28);

	return (
		<div style={{ width: "100%", height: chartHeight }}>
			<ResponsiveContainer width="100%" height="100%">
				<BarChart
					data={sorted}
					layout="vertical"
					margin={{ top: 8, right: 32, bottom: 8, left: 120 }}
				>
					<XAxis type="number" stroke="#555" tick={{ fill: "#888" }} />
					<YAxis
						type="category"
						dataKey="skill_norm"
						width={110}
						tick={{ fill: "#e0e0e0", fontSize: 12 }}
					/>
					<Tooltip
						content={<CustomTooltip />}
						cursor={{ fill: "rgba(37, 99, 235, 0.1)" }}
					/>
					<Bar dataKey="count" fill="#2563eb" radius={[0, 4, 4, 0]} />
				</BarChart>
			</ResponsiveContainer>
		</div>
	);
}

export default SkillBarChart;
