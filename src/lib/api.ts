import type {
	CoOccurrencePair,
	FilterState,
	GeoPoint,
	SalaryBucket,
	SkillDemand,
	SyncStatus,
	TrendPoint,
} from "../types";

const BASE = "http://localhost:8008/api/v1";

function buildParams(filters: FilterState): URLSearchParams {
	const params = new URLSearchParams();
	if (filters.canonical_role)
		params.set("canonical_role", filters.canonical_role);
	if (filters.location_region)
		params.set("location_region", filters.location_region);
	if (filters.date_from) params.set("date_from", filters.date_from);
	if (filters.date_to) params.set("date_to", filters.date_to);
	return params;
}

async function fetchJson<T>(url: string): Promise<T> {
	const res = await fetch(url);
	if (!res.ok) {
		const text = await res.text().catch(() => "Unknown error");
		throw new Error(`API ${res.status}: ${text}`);
	}
	return res.json() as Promise<T>;
}

export async function fetchRoles(): Promise<string[]> {
	return fetchJson<string[]>(`${BASE}/roles`);
}

export async function fetchRegions(): Promise<string[]> {
	return fetchJson<string[]>(`${BASE}/regions`);
}

export async function fetchSkillDemand(
	filters: FilterState,
	limit = 20,
): Promise<SkillDemand[]> {
	const params = buildParams(filters);
	params.set("limit", String(limit));
	return fetchJson<SkillDemand[]>(`${BASE}/skills/demand?${params.toString()}`);
}

export async function fetchCoOccurrence(
	limit = 50,
): Promise<CoOccurrencePair[]> {
	const params = new URLSearchParams({ limit: String(limit) });
	return fetchJson<CoOccurrencePair[]>(
		`${BASE}/skills/cooccurrence?${params.toString()}`,
	);
}

export async function fetchGeoDensity(
	filters: FilterState,
): Promise<GeoPoint[]> {
	const params = buildParams(filters);
	return fetchJson<GeoPoint[]>(`${BASE}/geo/density?${params.toString()}`);
}

export async function fetchSalaryDistribution(
	filters: FilterState,
): Promise<SalaryBucket[]> {
	const params = buildParams(filters);
	return fetchJson<SalaryBucket[]>(
		`${BASE}/salaries/distribution?${params.toString()}`,
	);
}

export async function fetchTrendSkills(
	filters: FilterState,
	skills?: string[],
): Promise<TrendPoint[]> {
	const params = buildParams(filters);
	if (skills && skills.length > 0) {
		params.set("skills", skills.join(","));
	}
	return fetchJson<TrendPoint[]>(`${BASE}/trends/skills?${params.toString()}`);
}

export async function fetchSyncStatus(): Promise<SyncStatus> {
	return fetchJson<SyncStatus>(`${BASE}/sync/status`);
}

export async function triggerSync(): Promise<void> {
	const res = await fetch(`${BASE}/sync/trigger`, { method: "POST" });
	if (!res.ok) {
		const text = await res.text().catch(() => "Unknown error");
		throw new Error(`Sync trigger failed: ${text}`);
	}
}
