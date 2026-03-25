import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { fetchSyncStatus, triggerSync } from "../lib/api";
import type { SyncStatus } from "../types";

export function useSyncStatus() {
	const [isSyncing, setIsSyncing] = useState(false);
	const queryClient = useQueryClient();
	const prevStatusRef = useRef<SyncStatus["status"] | null>(null);

	const { data: status } = useQuery({
		queryKey: ["syncStatus"],
		queryFn: fetchSyncStatus,
		refetchInterval: isSyncing ? 2000 : false,
	});

	useEffect(() => {
		if (!status) return;

		const prev = prevStatusRef.current;
		prevStatusRef.current = status.status;

		if (
			prev === "running" &&
			(status.status === "success" ||
				status.status === "error" ||
				status.status === "partial")
		) {
			setIsSyncing(false);
			void queryClient.invalidateQueries({
				predicate: (query) => query.queryKey[0] !== "syncStatus",
			});
		}

		if (status.status === "running" && !isSyncing) {
			setIsSyncing(true);
		}
	}, [status, isSyncing, queryClient]);

	const startSync = useCallback(async () => {
		setIsSyncing(true);
		try {
			await triggerSync();
		} catch (err: unknown) {
			const message = err instanceof Error ? err.message : String(err);
			console.error("Failed to trigger sync:", message);
			setIsSyncing(false);
		}
	}, []);

	return { status: status ?? null, isSyncing, startSync };
}
