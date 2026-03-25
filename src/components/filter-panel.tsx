import { useRegions, useRoles } from "../hooks/use-job-data";
import type { FilterState } from "../types";

interface FilterPanelProps {
	filters: FilterState;
	onChange: (filters: FilterState) => void;
}

const selectStyle: React.CSSProperties = {
	padding: "8px 12px",
	borderRadius: "6px",
	border: "1px solid #333",
	backgroundColor: "#0f0f1a",
	color: "#e0e0e0",
	fontSize: "0.875rem",
	minHeight: "40px",
	cursor: "pointer",
	outline: "none",
};

const inputStyle: React.CSSProperties = {
	...selectStyle,
	cursor: "text",
	colorScheme: "dark",
};

const labelStyle: React.CSSProperties = {
	fontSize: "0.75rem",
	fontWeight: 300,
	color: "#888",
	marginBottom: "4px",
};

function FilterPanel({ filters, onChange }: FilterPanelProps) {
	const { data: roles } = useRoles();
	const { data: regions } = useRegions();

	return (
		<div
			style={{
				display: "flex",
				gap: "16px",
				alignItems: "flex-end",
				padding: "12px 24px",
				backgroundColor: "#1a1a2e",
				borderBottom: "1px solid #333",
				flexWrap: "wrap",
			}}
		>
			<div style={{ display: "flex", flexDirection: "column" }}>
				<span style={labelStyle}>Role</span>
				<select
					style={selectStyle}
					value={filters.canonical_role ?? ""}
					onChange={(e) =>
						onChange({
							...filters,
							canonical_role: e.target.value || null,
						})
					}
				>
					<option value="">All Roles</option>
					{roles?.map((role) => (
						<option key={role} value={role}>
							{role}
						</option>
					))}
				</select>
			</div>

			<div style={{ display: "flex", flexDirection: "column" }}>
				<span style={labelStyle}>Region</span>
				<select
					style={selectStyle}
					value={filters.location_region ?? ""}
					onChange={(e) =>
						onChange({
							...filters,
							location_region: e.target.value || null,
						})
					}
				>
					<option value="">All Regions</option>
					{regions?.map((region) => (
						<option key={region} value={region}>
							{region}
						</option>
					))}
				</select>
			</div>

			<div style={{ display: "flex", flexDirection: "column" }}>
				<span style={labelStyle}>From</span>
				<input
					type="date"
					style={inputStyle}
					value={filters.date_from ?? ""}
					onChange={(e) =>
						onChange({
							...filters,
							date_from: e.target.value || null,
						})
					}
				/>
			</div>

			<div style={{ display: "flex", flexDirection: "column" }}>
				<span style={labelStyle}>To</span>
				<input
					type="date"
					style={inputStyle}
					value={filters.date_to ?? ""}
					onChange={(e) =>
						onChange({
							...filters,
							date_to: e.target.value || null,
						})
					}
				/>
			</div>
		</div>
	);
}

export default FilterPanel;
