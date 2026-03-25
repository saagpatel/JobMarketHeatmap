import { useEffect, useState } from "react";
import {
	Bar,
	CartesianGrid,
	Cell,
	ComposedChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import type { FilterState, SalaryBucket } from "../types";

const BASE = "http://localhost:8008/api/v1";

function buildParams(filters: FilterState): string {
	const p = new URLSearchParams();
	if (filters.canonical_role) p.set("canonical_role", filters.canonical_role);
	if (filters.location_region)
		p.set("location_region", filters.location_region);
	if (filters.date_from) p.set("date_from", filters.date_from);
	if (filters.date_to) p.set("date_to", filters.date_to);
	return p.toString();
}

function formatSalary(value: number): string {
	if (value >= 1000) {
		return `$${String(Math.round(value / 1000))}k`;
	}
	return `$${String(Math.round(value))}`;
}

interface ChartDatum {
	role: string;
	p25: number;
	median: number;
	p75: number;
	min: number;
	max: number;
	sample_size: number;
	boxBase: number;
	boxHeight: number;
}

function toChartData(buckets: SalaryBucket[]): ChartDatum[] {
	return buckets.map((b) => ({
		...b,
		boxBase: b.p25,
		boxHeight: b.p75 - b.p25,
	}));
}

interface BoxWhiskerShapeProps {
	x?: number;
	y?: number;
	width?: number;
	height?: number;
	payload?: ChartDatum;
}

function BoxWhiskerShape(props: BoxWhiskerShapeProps) {
	const { x = 0, y = 0, width = 0, height = 0, payload } = props;

	if (!payload || height === 0) return null;

	const yScale = height / (payload.p75 - payload.p25 || 1);
	const centerX = x + width / 2;
	const boxX = x + 4;
	const boxWidth = width - 8;

	const boxTop = y;
	const boxBottom = y + height;
	const medianY = boxTop + (payload.p75 - payload.median) * yScale;
	const minY = boxBottom + (payload.p25 - payload.min) * yScale;
	const maxY = boxTop - (payload.max - payload.p75) * yScale;
	const capHalf = 8;

	return (
		<g>
			{/* Lower whisker: min to p25 */}
			<line
				x1={centerX}
				y1={boxBottom}
				x2={centerX}
				y2={minY}
				stroke="#888"
				strokeWidth={1}
			/>
			{/* Min cap */}
			<line
				x1={centerX - capHalf}
				y1={minY}
				x2={centerX + capHalf}
				y2={minY}
				stroke="#888"
				strokeWidth={1}
			/>
			{/* Box: p25 to p75 */}
			<rect
				x={boxX}
				y={boxTop}
				width={boxWidth}
				height={height}
				fill="#2563eb"
				fillOpacity={0.8}
				stroke="#3b82f6"
				strokeWidth={1}
				rx={2}
			/>
			{/* Median line */}
			<line
				x1={boxX}
				y1={medianY}
				x2={boxX + boxWidth}
				y2={medianY}
				stroke="#fff"
				strokeWidth={2}
			/>
			{/* Upper whisker: p75 to max */}
			<line
				x1={centerX}
				y1={boxTop}
				x2={centerX}
				y2={maxY}
				stroke="#888"
				strokeWidth={1}
			/>
			{/* Max cap */}
			<line
				x1={centerX - capHalf}
				y1={maxY}
				x2={centerX + capHalf}
				y2={maxY}
				stroke="#888"
				strokeWidth={1}
			/>
		</g>
	);
}

interface CustomTooltipProps {
	active?: boolean;
	payload?: Array<{ payload: ChartDatum }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
	if (!active || !payload || payload.length === 0) return null;

	const d = payload[0].payload;
	return (
		<div
			style={{
				backgroundColor: "#1a1a2e",
				border: "1px solid #333",
				borderRadius: "8px",
				padding: "12px 16px",
				color: "#e0e0e0",
				fontSize: "0.8rem",
				lineHeight: 1.6,
			}}
		>
			<div style={{ fontWeight: 700, marginBottom: "4px", color: "#fff" }}>
				{d.role}
			</div>
			<div>Max: {formatSalary(d.max)}</div>
			<div>P75: {formatSalary(d.p75)}</div>
			<div style={{ color: "#3b82f6", fontWeight: 700 }}>
				Median: {formatSalary(d.median)}
			</div>
			<div>P25: {formatSalary(d.p25)}</div>
			<div>Min: {formatSalary(d.min)}</div>
			<div style={{ marginTop: "4px", color: "#888" }}>
				n = {String(d.sample_size)}
			</div>
		</div>
	);
}

interface SalaryBoxPlotProps {
	filters: FilterState;
}

function SalaryBoxPlot({ filters }: SalaryBoxPlotProps) {
	const [data, setData] = useState<SalaryBucket[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		let cancelled = false;

		async function fetchData() {
			setLoading(true);
			setError(null);

			try {
				const qs = buildParams(filters);
				const url = `${BASE}/salaries/distribution${qs ? `?${qs}` : ""}`;
				const res = await fetch(url);

				if (!res.ok) {
					throw new Error(`API returned ${String(res.status)}`);
				}

				const json: unknown = await res.json();
				if (
					typeof json === "object" &&
					json !== null &&
					"data" in json &&
					Array.isArray((json as Record<string, unknown>).data)
				) {
					if (!cancelled) {
						setData((json as Record<string, unknown>).data as SalaryBucket[]);
					}
				} else {
					throw new Error("Unexpected response shape");
				}
			} catch (err: unknown) {
				if (!cancelled) {
					const message = err instanceof Error ? err.message : String(err);
					setError(message);
					console.error("SalaryBoxPlot fetch error:", message);
				}
			} finally {
				if (!cancelled) {
					setLoading(false);
				}
			}
		}

		fetchData();
		return () => {
			cancelled = true;
		};
	}, [filters]);

	if (loading) {
		return (
			<div
				style={{
					width: "100%",
					height: "100%",
					display: "flex",
					alignItems: "center",
					justifyContent: "center",
					backgroundColor: "#0f0f1a",
					color: "#666",
					fontSize: "0.875rem",
				}}
			>
				Loading salary data...
			</div>
		);
	}

	if (error) {
		return (
			<div
				style={{
					width: "100%",
					height: "100%",
					display: "flex",
					alignItems: "center",
					justifyContent: "center",
					backgroundColor: "#0f0f1a",
					color: "#f87171",
					fontSize: "0.875rem",
				}}
			>
				Error: {error}
			</div>
		);
	}

	if (data.length === 0) {
		return (
			<div
				style={{
					width: "100%",
					height: "100%",
					display: "flex",
					alignItems: "center",
					justifyContent: "center",
					backgroundColor: "#0f0f1a",
					color: "#666",
					fontSize: "0.875rem",
				}}
			>
				<div style={{ textAlign: "center" }}>
					<p style={{ fontSize: "1.1rem", margin: "0 0 8px" }}>No data yet</p>
					<p style={{ fontSize: "0.85rem", margin: 0, color: "#555" }}>
						Click &ldquo;Sync Now&rdquo; to fetch job postings
					</p>
				</div>
			</div>
		);
	}

	const chartData = toChartData(data);
	const yMin = Math.floor(Math.min(...data.map((d) => d.min)) / 10000) * 10000;
	const yMax = Math.ceil(Math.max(...data.map((d) => d.max)) / 10000) * 10000;

	return (
		<div
			style={{
				width: "100%",
				height: "100%",
				backgroundColor: "#0f0f1a",
				padding: "16px",
				boxSizing: "border-box",
			}}
		>
			<ResponsiveContainer width="100%" height="100%">
				<ComposedChart
					data={chartData}
					margin={{ top: 20, right: 20, bottom: 60, left: 20 }}
				>
					<CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
					<XAxis
						dataKey="role"
						tick={{
							fill: "#888",
							fontSize: 11,
						}}
						angle={-35}
						textAnchor="end"
						interval={0}
						axisLine={{ stroke: "#333" }}
						tickLine={{ stroke: "#333" }}
					/>
					<YAxis
						domain={[yMin, yMax]}
						tickFormatter={formatSalary}
						tick={{ fill: "#888", fontSize: 11 }}
						axisLine={{ stroke: "#333" }}
						tickLine={{ stroke: "#333" }}
					/>
					<Tooltip content={<CustomTooltip />} />
					<Bar
						dataKey="boxHeight"
						stackId="salary"
						shape={<BoxWhiskerShape />}
						isAnimationActive={false}
					>
						{chartData.map((entry) => (
							<Cell key={entry.role} fill="#2563eb" />
						))}
					</Bar>
				</ComposedChart>
			</ResponsiveContainer>
		</div>
	);
}

export default SalaryBoxPlot;
