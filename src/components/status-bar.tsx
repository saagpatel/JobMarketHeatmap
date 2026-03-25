import { useSyncStatus } from "../hooks/use-sync-status";

function formatTime(iso: string | null): string {
	if (!iso) return "Never";
	const date = new Date(iso);
	return date.toLocaleString();
}

function StatusBar() {
	const { status, isSyncing, startSync } = useSyncStatus();

	const jobCount = status ? status.jobs_inserted + status.jobs_skipped : 0;

	return (
		<div
			style={{
				display: "flex",
				justifyContent: "space-between",
				alignItems: "center",
				padding: "8px 24px",
				backgroundColor: "#1a1a2e",
				borderTop: "1px solid #333",
				fontSize: "0.8rem",
				color: "#888",
				flexShrink: 0,
			}}
		>
			<div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
				<span>Last sync: {formatTime(status?.last_sync ?? null)}</span>
				<span>{jobCount} jobs</span>
				{status?.status === "error" && status.error_message && (
					<span style={{ color: "#f87171" }}>{status.error_message}</span>
				)}
			</div>
			<button
				onClick={() => void startSync()}
				disabled={isSyncing}
				style={{
					padding: "6px 16px",
					borderRadius: "6px",
					border: "1px solid #333",
					backgroundColor: isSyncing ? "transparent" : "#2563eb",
					color: isSyncing ? "#888" : "#fff",
					fontSize: "0.8rem",
					fontWeight: 700,
					cursor: isSyncing ? "not-allowed" : "pointer",
					opacity: isSyncing ? 0.6 : 1,
					minHeight: "32px",
					transition: "background-color 150ms ease, opacity 150ms ease",
				}}
			>
				{isSyncing ? "Syncing..." : "Sync Now"}
			</button>
		</div>
	);
}

export default StatusBar;
