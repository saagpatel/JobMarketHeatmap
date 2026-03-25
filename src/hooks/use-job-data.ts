import { useQuery } from "@tanstack/react-query";
import * as api from "../lib/api";
import type { FilterState } from "../types";

export function useRoles() {
	return useQuery({ queryKey: ["roles"], queryFn: api.fetchRoles });
}

export function useRegions() {
	return useQuery({ queryKey: ["regions"], queryFn: api.fetchRegions });
}

export function useSkillDemand(filters: FilterState) {
	return useQuery({
		queryKey: ["skillDemand", filters],
		queryFn: () => api.fetchSkillDemand(filters),
	});
}

export function useCoOccurrence(limit = 50) {
	return useQuery({
		queryKey: ["coOccurrence", limit],
		queryFn: () => api.fetchCoOccurrence(limit),
	});
}

export function useGeoDensity(filters: FilterState) {
	return useQuery({
		queryKey: ["geoDensity", filters],
		queryFn: () => api.fetchGeoDensity(filters),
	});
}

export function useSalaryDistribution(filters: FilterState) {
	return useQuery({
		queryKey: ["salaryDistribution", filters],
		queryFn: () => api.fetchSalaryDistribution(filters),
	});
}

export function useTrendSkills(filters: FilterState, skills?: string[]) {
	return useQuery({
		queryKey: ["trendSkills", filters, skills],
		queryFn: () => api.fetchTrendSkills(filters, skills),
	});
}
