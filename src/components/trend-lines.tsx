import { useMemo } from "react";
import {
	Legend,
	Line,
	LineChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import { useTrendSkills } from "../hooks/use-job-data";
import type { FilterState } from "../types";

interface TrendLinesProps {
	filters: FilterState;
}

const PALETTE = [
	"#2563eb",
	"#06b6d4",
	"#10b981",
	"#f59e0b",
	"#ef4444",
	"#8b5cf6",
	"#ec4899",
	"#14b8a6",
	"#f97316",
	"#6366f1",
];

function TrendLines({ filters }: TrendLinesProps) {
	const { data, isLoading } = useTrendSkills(filters);

	const { pivoted, skills } = useMemo(() => {
		if (!data || data.length === 0) return { pivoted: [], skills: [] };

		const skillSet = new Set<string>();
		const weekMap = new Map<string, Record<string, number>>();

		for (const point of data) {
			skillSet.add(point.skill);
			const existing = weekMap.get(point.week) ?? {};
			existing[point.skill] = point.count;
			weekMap.set(point.week, existing);
		}

		const sortedWeeks = [...weekMap.keys()].sort();
		const skillList = [...skillSet];

		const rows = sortedWeeks.map((week) => {
			const row: Record<string, string | number> = { week };
			const weekData = weekMap.get(week);
			for (const skill of skillList) {
				row[skill] = weekData?.[skill] ?? 0;
			}
			return row;
		});

		return { pivoted: rows, skills: skillList };
	}, [data]);

	if (isLoading) {
		return (
			<div style={{ color: "#888", padding: "2rem", textAlign: "center" }}>
				Loading trends...
			</div>
		);
	}

	if (pivoted.length === 0) {
		return (
			<div style={{ color: "#555", padding: "4rem", textAlign: "center" }}>
				<p style={{ fontSize: "1.1rem", margin: "0 0 8px" }}>No data yet</p>
				<p style={{ fontSize: "0.85rem", margin: 0 }}>
					Click &ldquo;Sync Now&rdquo; to fetch job postings
				</p>
			</div>
		);
	}

	return (
		<div style={{ width: "100%", height: 480 }}>
			<ResponsiveContainer width="100%" height="100%">
				<LineChart
					data={pivoted}
					margin={{ top: 8, right: 32, bottom: 8, left: 16 }}
				>
					<XAxis
						dataKey="week"
						stroke="#555"
						tick={{ fill: "#888", fontSize: 12 }}
					/>
					<YAxis stroke="#555" tick={{ fill: "#888" }} />
					<Tooltip
						contentStyle={{
							backgroundColor: "#1a1a2e",
							border: "1px solid #333",
							borderRadius: "6px",
							color: "#e0e0e0",
						}}
					/>
					<Legend wrapperStyle={{ color: "#e0e0e0", paddingTop: "8px" }} />
					{skills.map((skill, i) => (
						<Line
							key={skill}
							type="monotone"
							dataKey={skill}
							stroke={PALETTE[i % PALETTE.length]}
							strokeWidth={2}
							dot={false}
							activeDot={{ r: 4 }}
						/>
					))}
				</LineChart>
			</ResponsiveContainer>
		</div>
	);
}

export default TrendLines;
