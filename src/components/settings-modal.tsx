import { invoke } from "@tauri-apps/api/core";
import { useCallback, useEffect, useState } from "react";

const SIDECAR_URL = "http://localhost:8008";

interface SettingsModalProps {
	onClose: () => void;
}

type FeedbackKind = "success" | "error";

interface Feedback {
	kind: FeedbackKind;
	message: string;
}

const inputStyle: React.CSSProperties = {
	width: "100%",
	padding: "10px 12px",
	borderRadius: "6px",
	border: "1px solid #333",
	backgroundColor: "#0f0f1a",
	color: "#e0e0e0",
	fontSize: "0.9rem",
	boxSizing: "border-box",
};

const labelTextStyle: React.CSSProperties = {
	display: "block",
	marginBottom: "6px",
	fontSize: "0.875rem",
	fontWeight: 300,
};

function SettingsModal({ onClose }: SettingsModalProps) {
	const [appId, setAppId] = useState("");
	const [appKey, setAppKey] = useState("");
	const [syncHour, setSyncHour] = useState(2);
	const [syncMinute, setSyncMinute] = useState(0);
	const [feedback, setFeedback] = useState<Feedback | null>(null);
	const [saving, setSaving] = useState(false);
	const [testing, setTesting] = useState(false);

	useEffect(() => {
		async function loadSettings() {
			// Load credentials
			try {
				const creds = await invoke<[string, string] | null>("get_credentials");
				if (creds) {
					setAppId(creds[0]);
					setAppKey(creds[1]);
				}
			} catch {
				// Tauri not available
			}

			// Load schedule
			try {
				const res = await fetch(`${SIDECAR_URL}/api/v1/sync/schedule`);
				if (res.ok) {
					const data = (await res.json()) as {
						hour: number;
						minute: number;
					};
					setSyncHour(data.hour);
					setSyncMinute(data.minute);
				}
			} catch {
				// Sidecar not available
			}
		}
		loadSettings();
	}, []);

	const handleSave = useCallback(async () => {
		if (!appId.trim() || !appKey.trim()) {
			setFeedback({ kind: "error", message: "Both fields are required." });
			return;
		}

		setSaving(true);
		setFeedback(null);

		try {
			// Save credentials
			await invoke("set_credentials", {
				appId: appId.trim(),
				appKey: appKey.trim(),
			});

			const credRes = await fetch(`${SIDECAR_URL}/api/v1/credentials`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					app_id: appId.trim(),
					app_key: appKey.trim(),
				}),
			});
			if (!credRes.ok) {
				throw new Error(`Sidecar responded with ${String(credRes.status)}`);
			}

			// Save schedule
			const schedRes = await fetch(`${SIDECAR_URL}/api/v1/sync/schedule`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ hour: syncHour, minute: syncMinute }),
			});
			if (!schedRes.ok) {
				throw new Error(`Schedule update failed: ${String(schedRes.status)}`);
			}

			setFeedback({ kind: "success", message: "Settings saved." });
		} catch (err: unknown) {
			const message = err instanceof Error ? err.message : String(err);
			setFeedback({ kind: "error", message: `Save failed: ${message}` });
		} finally {
			setSaving(false);
		}
	}, [appId, appKey, syncHour, syncMinute]);

	const handleTest = useCallback(async () => {
		setTesting(true);
		setFeedback(null);

		try {
			const res = await fetch(`${SIDECAR_URL}/api/v1/sync/test`);
			if (!res.ok) {
				throw new Error(`Status ${String(res.status)}`);
			}
			const data = (await res.json()) as {
				connected: boolean;
				jobs_available: number;
				error: string | null;
			};
			if (data.connected) {
				setFeedback({
					kind: "success",
					message: `Connected — ${String(data.jobs_available)} job(s) found`,
				});
			} else {
				setFeedback({
					kind: "error",
					message: data.error ?? "Connection failed",
				});
			}
		} catch (err: unknown) {
			const message = err instanceof Error ? err.message : String(err);
			setFeedback({
				kind: "error",
				message: `Connection failed: ${message}`,
			});
		} finally {
			setTesting(false);
		}
	}, []);

	return (
		<div
			style={{
				position: "fixed",
				inset: 0,
				backgroundColor: "rgba(0, 0, 0, 0.5)",
				display: "flex",
				alignItems: "center",
				justifyContent: "center",
				zIndex: 1000,
			}}
			onClick={onClose}
		>
			<div
				style={{
					backgroundColor: "#1a1a2e",
					color: "#e0e0e0",
					borderRadius: "12px",
					padding: "32px",
					width: "420px",
					maxWidth: "90vw",
					maxHeight: "90vh",
					overflowY: "auto",
					boxShadow: "0 8px 32px rgba(0, 0, 0, 0.4)",
				}}
				onClick={(e) => e.stopPropagation()}
			>
				<div
					style={{
						display: "flex",
						justifyContent: "space-between",
						alignItems: "center",
						marginBottom: "24px",
					}}
				>
					<h2 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 700 }}>
						Settings
					</h2>
					<button
						onClick={onClose}
						style={{
							background: "none",
							border: "none",
							color: "#888",
							fontSize: "1.5rem",
							cursor: "pointer",
							padding: "4px",
							lineHeight: 1,
						}}
					>
						&times;
					</button>
				</div>

				{/* Credentials section */}
				<h3
					style={{
						fontSize: "0.9rem",
						fontWeight: 700,
						color: "#888",
						margin: "0 0 12px",
						textTransform: "uppercase",
						letterSpacing: "0.05em",
					}}
				>
					Adzuna API
				</h3>

				<label style={{ display: "block", marginBottom: "16px" }}>
					<span style={labelTextStyle}>App ID</span>
					<input
						type="text"
						value={appId}
						onChange={(e) => setAppId(e.target.value)}
						placeholder="Your Adzuna App ID"
						style={inputStyle}
					/>
				</label>

				<label style={{ display: "block", marginBottom: "24px" }}>
					<span style={labelTextStyle}>App Key</span>
					<input
						type="password"
						value={appKey}
						onChange={(e) => setAppKey(e.target.value)}
						placeholder="Your Adzuna App Key"
						style={inputStyle}
					/>
				</label>

				{/* Schedule section */}
				<h3
					style={{
						fontSize: "0.9rem",
						fontWeight: 700,
						color: "#888",
						margin: "0 0 12px",
						textTransform: "uppercase",
						letterSpacing: "0.05em",
					}}
				>
					Sync Schedule
				</h3>

				<div
					style={{
						display: "flex",
						gap: "12px",
						marginBottom: "24px",
						alignItems: "end",
					}}
				>
					<label style={{ flex: 1 }}>
						<span style={labelTextStyle}>Hour (0-23)</span>
						<input
							type="number"
							min={0}
							max={23}
							value={syncHour}
							onChange={(e) => setSyncHour(Number(e.target.value))}
							style={inputStyle}
						/>
					</label>
					<label style={{ flex: 1 }}>
						<span style={labelTextStyle}>Minute (0-59)</span>
						<input
							type="number"
							min={0}
							max={59}
							value={syncMinute}
							onChange={(e) => setSyncMinute(Number(e.target.value))}
							style={inputStyle}
						/>
					</label>
				</div>

				{feedback && (
					<div
						style={{
							padding: "10px 12px",
							borderRadius: "6px",
							marginBottom: "16px",
							fontSize: "0.875rem",
							backgroundColor:
								feedback.kind === "success" ? "#0a2e1a" : "#2e0a0a",
							color: feedback.kind === "success" ? "#4ade80" : "#f87171",
							border: `1px solid ${feedback.kind === "success" ? "#166534" : "#7f1d1d"}`,
						}}
					>
						{feedback.message}
					</div>
				)}

				<div style={{ display: "flex", gap: "12px" }}>
					<button
						onClick={handleSave}
						disabled={saving}
						style={{
							flex: 1,
							padding: "10px 16px",
							borderRadius: "6px",
							border: "none",
							backgroundColor: "#2563eb",
							color: "#fff",
							fontWeight: 700,
							fontSize: "0.9rem",
							cursor: saving ? "not-allowed" : "pointer",
							opacity: saving ? 0.6 : 1,
							minHeight: "40px",
						}}
					>
						{saving ? "Saving..." : "Save"}
					</button>
					<button
						onClick={handleTest}
						disabled={testing}
						style={{
							flex: 1,
							padding: "10px 16px",
							borderRadius: "6px",
							border: "1px solid #333",
							backgroundColor: "transparent",
							color: "#e0e0e0",
							fontWeight: 700,
							fontSize: "0.9rem",
							cursor: testing ? "not-allowed" : "pointer",
							opacity: testing ? 0.6 : 1,
							minHeight: "40px",
						}}
					>
						{testing ? "Testing..." : "Test Connection"}
					</button>
				</div>
			</div>
		</div>
	);
}

export default SettingsModal;
