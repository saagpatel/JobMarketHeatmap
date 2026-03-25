import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { invoke } from "@tauri-apps/api/core";
import { load } from "@tauri-apps/plugin-store";
import { useCallback, useEffect, useState } from "react";
import CoOccurrenceGraph from "./components/co-occurrence-graph";
import ErrorBoundary from "./components/error-boundary";
import FilterPanel from "./components/filter-panel";
import GeoHeatmap from "./components/geo-heatmap";
import SalaryBoxPlot from "./components/salary-box-plot";
import SettingsModal from "./components/settings-modal";
import SkillBarChart from "./components/skill-bar-chart";
import StatusBar from "./components/status-bar";
import TrendLines from "./components/trend-lines";
import type { FilterState } from "./types";

const SIDECAR_URL = "http://localhost:8008";

type Tab = "skills" | "map" | "salary" | "graph" | "trends";

const TABS: { key: Tab; label: string }[] = [
	{ key: "skills", label: "Skill Demand" },
	{ key: "map", label: "Map" },
	{ key: "salary", label: "Salary" },
	{ key: "graph", label: "Co-occurrence" },
	{ key: "trends", label: "Trends" },
];

const DEFAULT_FILTERS: FilterState = {
	canonical_role: null,
	location_region: null,
	date_from: null,
	date_to: null,
};

const queryClient = new QueryClient({
	defaultOptions: {
		queries: {
			staleTime: 30_000,
			retry: 2,
			retryDelay: 1000,
		},
	},
});

function tabButtonStyle(isActive: boolean): React.CSSProperties {
	return {
		padding: "8px 16px",
		borderRadius: "6px",
		border: "none",
		backgroundColor: isActive ? "#2563eb" : "transparent",
		color: isActive ? "#fff" : "#888",
		fontSize: "0.875rem",
		fontWeight: isActive ? 700 : 300,
		cursor: "pointer",
		minHeight: "40px",
		transition: "background-color 150ms ease, color 150ms ease",
	};
}

function AppContent() {
	const [activeTab, setActiveTab] = useState<Tab>("skills");
	const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
	const [showSettings, setShowSettings] = useState(false);

	// Hydrate credentials + restore persisted filters on mount
	useEffect(() => {
		async function init() {
			// Restore filters
			try {
				const store = await load("filters.json");
				const saved = await store.get<FilterState>("filter_state");
				if (saved) setFilters(saved);
			} catch {
				// Store not available (e.g. running outside Tauri) — use defaults
			}

			// Hydrate credentials to sidecar
			try {
				const creds = await invoke<[string, string] | null>("get_credentials");
				if (creds) {
					await fetch(`${SIDECAR_URL}/api/v1/credentials`, {
						method: "POST",
						headers: { "Content-Type": "application/json" },
						body: JSON.stringify({
							app_id: creds[0],
							app_key: creds[1],
						}),
					});
				}
			} catch (err: unknown) {
				const message = err instanceof Error ? err.message : String(err);
				console.warn("Could not hydrate credentials:", message);
			}
		}
		init();
	}, []);

	// Persist filters on change
	const handleFilterChange = useCallback((newFilters: FilterState) => {
		setFilters(newFilters);
		load("filters.json")
			.then((store) => store.set("filter_state", newFilters))
			.catch(() => {
				// Store not available outside Tauri
			});
	}, []);

	return (
		<div
			style={{
				display: "flex",
				flexDirection: "column",
				height: "100vh",
				backgroundColor: "#0f0f1a",
				color: "#e0e0e0",
				fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
			}}
		>
			<header
				style={{
					display: "flex",
					justifyContent: "space-between",
					alignItems: "center",
					padding: "12px 24px",
					backgroundColor: "#1a1a2e",
					borderBottom: "1px solid #333",
					flexShrink: 0,
				}}
			>
				<h1
					style={{
						margin: 0,
						fontSize: "1.1rem",
						fontWeight: 700,
						color: "#e0e0e0",
						letterSpacing: "0.02em",
					}}
				>
					Job Market Heatmap
				</h1>
				<nav style={{ display: "flex", gap: "4px" }}>
					{TABS.map((tab) => (
						<button
							key={tab.key}
							style={tabButtonStyle(activeTab === tab.key)}
							onClick={() => setActiveTab(tab.key)}
						>
							{tab.label}
						</button>
					))}
				</nav>
				<button
					onClick={() => setShowSettings(true)}
					style={{
						background: "none",
						border: "1px solid #333",
						borderRadius: "6px",
						color: "#888",
						fontSize: "1.2rem",
						cursor: "pointer",
						padding: "6px 10px",
						minHeight: "40px",
						transition: "border-color 150ms ease",
					}}
					title="Settings"
				>
					&#9881;
				</button>
			</header>

			<FilterPanel filters={filters} onChange={handleFilterChange} />

			<main
				style={{
					flex: 1,
					overflow: "auto",
					padding: "1rem",
				}}
			>
				<ErrorBoundary>
					{activeTab === "skills" && <SkillBarChart filters={filters} />}
					{activeTab === "map" && <GeoHeatmap filters={filters} />}
					{activeTab === "salary" && <SalaryBoxPlot filters={filters} />}
					{activeTab === "graph" && <CoOccurrenceGraph />}
					{activeTab === "trends" && <TrendLines filters={filters} />}
				</ErrorBoundary>
			</main>

			<StatusBar />

			{showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
		</div>
	);
}

function App() {
	return (
		<QueryClientProvider client={queryClient}>
			<AppContent />
		</QueryClientProvider>
	);
}

export default App;
