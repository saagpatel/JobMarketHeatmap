import { useCallback, useEffect, useRef, useState } from "react";
import { DataSet, Network } from "vis-network/standalone";
import type { CoOccurrencePair } from "../types";

const BASE = "http://localhost:8008/api/v1";

interface SkillInfo {
	name: string;
	totalCount: number;
	connections: number;
}

interface NodeData {
	id: string;
	label: string;
	size: number;
	totalCount: number;
	connections: number;
}

interface EdgeData {
	from: string;
	to: string;
	width: number;
	value: number;
}

function buildGraph(pairs: CoOccurrencePair[]): {
	nodes: NodeData[];
	edges: EdgeData[];
} {
	const skillCounts = new Map<string, number>();
	const skillConnections = new Map<string, number>();

	for (const pair of pairs) {
		skillCounts.set(
			pair.skill_a,
			(skillCounts.get(pair.skill_a) ?? 0) + pair.count,
		);
		skillCounts.set(
			pair.skill_b,
			(skillCounts.get(pair.skill_b) ?? 0) + pair.count,
		);
		skillConnections.set(
			pair.skill_a,
			(skillConnections.get(pair.skill_a) ?? 0) + 1,
		);
		skillConnections.set(
			pair.skill_b,
			(skillConnections.get(pair.skill_b) ?? 0) + 1,
		);
	}

	const maxCount = Math.max(...skillCounts.values(), 1);
	const minSize = 10;
	const maxSize = 40;

	const nodes: NodeData[] = [];
	for (const [skill, count] of skillCounts) {
		const normalized = count / maxCount;
		nodes.push({
			id: skill,
			label: skill,
			size: minSize + normalized * (maxSize - minSize),
			totalCount: count,
			connections: skillConnections.get(skill) ?? 0,
		});
	}

	const maxWeight = Math.max(...pairs.map((p) => p.weight), 1);
	const edges: EdgeData[] = pairs.map((pair) => ({
		from: pair.skill_a,
		to: pair.skill_b,
		width: 1 + (pair.weight / maxWeight) * 7,
		value: pair.count,
	}));

	return { nodes, edges };
}

function CoOccurrenceGraph() {
	const containerRef = useRef<HTMLDivElement>(null);
	const networkRef = useRef<Network | null>(null);
	const [selectedSkill, setSelectedSkill] = useState<SkillInfo | null>(null);
	const [data, setData] = useState<CoOccurrencePair[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		let cancelled = false;

		async function fetchData() {
			setLoading(true);
			setError(null);

			try {
				const res = await fetch(`${BASE}/skills/cooccurrence`);
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
						setData(
							(json as Record<string, unknown>).data as CoOccurrencePair[],
						);
					}
				} else {
					throw new Error("Unexpected response shape");
				}
			} catch (err: unknown) {
				if (!cancelled) {
					const message = err instanceof Error ? err.message : String(err);
					setError(message);
					console.error("CoOccurrenceGraph fetch error:", message);
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
	}, []);

	const handleClick = useCallback(
		(params: { nodes: string[] }) => {
			if (params.nodes.length > 0) {
				const nodeId = params.nodes[0];
				const graph = buildGraph(data);
				const node = graph.nodes.find((n) => n.id === nodeId);
				if (node) {
					setSelectedSkill({
						name: node.label,
						totalCount: node.totalCount,
						connections: node.connections,
					});
				}
			} else {
				setSelectedSkill(null);
			}
		},
		[data],
	);

	useEffect(() => {
		if (!containerRef.current || data.length === 0) return;

		const { nodes, edges } = buildGraph(data);

		const nodeDataSet = new DataSet(
			nodes.map((n) => ({
				id: n.id,
				label: n.label,
				size: n.size,
				font: { color: "#e0e0e0", size: 12 },
				color: {
					background: "#2563eb",
					border: "#1d4ed8",
					highlight: { background: "#3b82f6", border: "#60a5fa" },
					hover: { background: "#3b82f6", border: "#60a5fa" },
				},
				shape: "dot" as const,
			})),
		);

		const edgeDataSet = new DataSet(
			edges.map((e, i) => ({
				id: String(i),
				from: e.from,
				to: e.to,
				width: e.width,
				value: e.value,
				color: {
					color: "#444",
					highlight: "#06b6d4",
					hover: "#06b6d4",
				},
			})),
		);

		const options = {
			nodes: {
				font: { color: "#e0e0e0", size: 12 },
				borderWidth: 2,
			},
			edges: {
				smooth: {
					enabled: true,
					type: "continuous",
					roundness: 0.5,
					forceDirection: false,
				},
			},
			physics: {
				forceAtlas2Based: {
					gravitationalConstant: -30,
					springLength: 100,
					springConstant: 0.04,
				},
				solver: "forceAtlas2Based" as const,
				stabilization: { iterations: 150 },
			},
			interaction: {
				hover: true,
				tooltipDelay: 200,
			},
		};

		if (networkRef.current) {
			networkRef.current.destroy();
		}

		const network = new Network(
			containerRef.current,
			{ nodes: nodeDataSet, edges: edgeDataSet },
			options,
		);

		network.on("click", handleClick);
		networkRef.current = network;

		return () => {
			network.off("click", handleClick);
			network.destroy();
			networkRef.current = null;
		};
	}, [data, handleClick]);

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
				Loading co-occurrence data...
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

	return (
		<div
			style={{
				width: "100%",
				height: "100%",
				display: "flex",
				flexDirection: "column",
				backgroundColor: "#0f0f1a",
			}}
		>
			<div
				ref={containerRef}
				style={{
					flex: 1,
					minHeight: 0,
				}}
			/>
			{selectedSkill && (
				<div
					style={{
						padding: "12px 16px",
						backgroundColor: "#1a1a2e",
						borderTop: "1px solid #333",
						color: "#e0e0e0",
						fontSize: "0.8rem",
						display: "flex",
						justifyContent: "space-between",
						alignItems: "center",
					}}
				>
					<div>
						<span style={{ fontWeight: 700, color: "#3b82f6" }}>
							{selectedSkill.name}
						</span>
						<span style={{ color: "#888", marginLeft: "12px" }}>
							{String(selectedSkill.totalCount)} co-occurrences
						</span>
						<span style={{ color: "#888", marginLeft: "12px" }}>
							{String(selectedSkill.connections)} connections
						</span>
					</div>
					<button
						onClick={() => setSelectedSkill(null)}
						style={{
							background: "none",
							border: "none",
							color: "#888",
							cursor: "pointer",
							fontSize: "1rem",
							padding: "0 4px",
						}}
					>
						&times;
					</button>
				</div>
			)}
		</div>
	);
}

export default CoOccurrenceGraph;
