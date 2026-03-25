export interface Job {
	id: number;
	adzuna_id: string;
	title: string;
	company: string | null;
	location_city: string | null;
	location_region: string | null;
	location_lat: number | null;
	location_lon: number | null;
	salary_min: number | null;
	salary_max: number | null;
	salary_is_estimated: boolean;
	canonical_role: string | null;
	fetched_at: string;
}

export interface SkillDemand {
	skill_norm: string;
	count: number;
	pct_of_postings: number;
}

export interface CoOccurrencePair {
	skill_a: string;
	skill_b: string;
	count: number;
	weight: number;
}

export interface GeoPoint {
	lat: number;
	lon: number;
	city: string;
	count: number;
}

export interface SalaryBucket {
	role: string;
	p25: number;
	median: number;
	p75: number;
	min: number;
	max: number;
	sample_size: number;
}

export interface TrendPoint {
	week: string;
	skill: string;
	count: number;
}

export interface SyncStatus {
	status: "idle" | "running" | "success" | "error" | "partial";
	last_sync: string | null;
	jobs_fetched: number;
	jobs_inserted: number;
	jobs_skipped: number;
	error_message: string | null;
}

export interface FilterState {
	canonical_role: string | null;
	location_region: string | null;
	date_from: string | null;
	date_to: string | null;
}
