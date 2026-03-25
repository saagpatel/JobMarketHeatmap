import type { ErrorInfo, ReactNode } from "react";
import { Component } from "react";

interface ErrorBoundaryProps {
	children: ReactNode;
}

interface ErrorBoundaryState {
	hasError: boolean;
	error: Error | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
	constructor(props: ErrorBoundaryProps) {
		super(props);
		this.state = { hasError: false, error: null };
	}

	static getDerivedStateFromError(error: Error): ErrorBoundaryState {
		return { hasError: true, error };
	}

	componentDidCatch(error: Error, info: ErrorInfo): void {
		console.error("ErrorBoundary caught:", error, info);
	}

	render() {
		if (this.state.hasError) {
			return (
				<div
					style={{
						display: "flex",
						flexDirection: "column",
						alignItems: "center",
						justifyContent: "center",
						padding: "3rem",
						gap: "1rem",
					}}
				>
					<div
						style={{
							padding: "16px 24px",
							borderRadius: "8px",
							backgroundColor: "#2e0a0a",
							border: "1px solid #7f1d1d",
							color: "#f87171",
							textAlign: "center",
							maxWidth: "500px",
						}}
					>
						<p
							style={{
								margin: "0 0 8px",
								fontWeight: 700,
								fontSize: "1rem",
							}}
						>
							Something went wrong
						</p>
						<p
							style={{
								margin: 0,
								fontSize: "0.85rem",
								color: "#fca5a5",
							}}
						>
							{this.state.error?.message ??
								"Backend unavailable — check that the sidecar is running"}
						</p>
					</div>
					<button
						onClick={() => this.setState({ hasError: false, error: null })}
						style={{
							padding: "10px 24px",
							borderRadius: "6px",
							border: "none",
							backgroundColor: "#2563eb",
							color: "#fff",
							fontWeight: 700,
							fontSize: "0.9rem",
							cursor: "pointer",
							minHeight: "40px",
						}}
					>
						Retry
					</button>
				</div>
			);
		}

		return this.props.children;
	}
}

export default ErrorBoundary;
