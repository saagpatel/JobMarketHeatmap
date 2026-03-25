import L from "leaflet";
import { useEffect, useMemo, useState } from "react";
import {
	CircleMarker,
	MapContainer,
	Popup,
	TileLayer,
	useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.heat";
import type { FilterState, GeoPoint } from "../types";

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

function HeatLayer({ points }: { points: Array<[number, number, number]> }) {
	const map = useMap();

	useEffect(() => {
		if (points.length === 0) return;

		const heat = L.heatLayer(points, {
			radius: 25,
			blur: 15,
			maxZoom: 10,
			max: 1.0,
			gradient: {
				0.2: "#0d47a1",
				0.4: "#1565c0",
				0.6: "#42a5f5",
				0.8: "#ef6c00",
				1.0: "#ff5722",
			},
		});
		heat.addTo(map);

		return () => {
			map.removeLayer(heat);
		};
	}, [map, points]);

	return null;
}

interface GeoHeatmapProps {
	filters: FilterState;
}

function GeoHeatmap({ filters }: GeoHeatmapProps) {
	const [data, setData] = useState<GeoPoint[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		let cancelled = false;

		async function fetchData() {
			setLoading(true);
			setError(null);

			try {
				const qs = buildParams(filters);
				const url = `${BASE}/geo/density${qs ? `?${qs}` : ""}`;
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
						setData((json as Record<string, unknown>).data as GeoPoint[]);
					}
				} else {
					throw new Error("Unexpected response shape");
				}
			} catch (err: unknown) {
				if (!cancelled) {
					const message = err instanceof Error ? err.message : String(err);
					setError(message);
					console.error("GeoHeatmap fetch error:", message);
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

	const heatPoints = useMemo<Array<[number, number, number]>>(() => {
		if (data.length === 0) return [];
		const maxCount = Math.max(...data.map((p) => p.count));
		return data.map((p) => [
			p.lat,
			p.lon,
			maxCount > 0 ? p.count / maxCount : 0,
		]);
	}, [data]);

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
				Loading geographic data...
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
		<div style={{ width: "100%", height: "100%", position: "relative" }}>
			<MapContainer
				center={[39.8, -98.5]}
				zoom={4}
				style={{ width: "100%", height: "100%" }}
				zoomControl={true}
			>
				<TileLayer
					attribution='&copy; <a href="https://carto.com/">CARTO</a>'
					url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
				/>
				<HeatLayer points={heatPoints} />
				{data.map((point) => (
					<CircleMarker
						key={`${String(point.lat)}-${String(point.lon)}-${point.city}`}
						center={[point.lat, point.lon]}
						radius={Math.max(
							4,
							Math.min(
								16,
								4 + (point.count / Math.max(...data.map((p) => p.count))) * 12,
							),
						)}
						pathOptions={{
							color: "#2563eb",
							fillColor: "#3b82f6",
							fillOpacity: 0.6,
							weight: 1,
						}}
					>
						<Popup>
							<div
								style={{
									color: "#1a1a2e",
									fontWeight: 700,
									fontSize: "0.875rem",
								}}
							>
								{point.city}: {String(point.count)} jobs
							</div>
						</Popup>
					</CircleMarker>
				))}
			</MapContainer>
		</div>
	);
}

export default GeoHeatmap;
