import { defaultFilters } from "@/lib/defaults";
import type {
  DashboardFilters,
  DataPreview,
  FeedbackDashboardData,
  RagResponse,
  SalesDashboardData,
} from "@/lib/types";

const API_BASE_URL = "/api/backend";

function createSearchParams(filters: DashboardFilters) {
  const params = new URLSearchParams();

  if (filters.product && filters.product !== defaultFilters.product) {
    params.set("product", filters.product);
  }

  if (filters.country && filters.country !== defaultFilters.country) {
    params.set("country", filters.country);
  }

  if (filters.region && filters.region !== defaultFilters.region) {
    params.set("region", filters.region);
  }

  params.set("date_from", filters.dateFrom);
  params.set("date_to", filters.dateTo);

  return params.toString();
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function getSalesDashboard(
  filters: DashboardFilters,
): Promise<SalesDashboardData> {
  const params = createSearchParams(filters);
  return fetchJson<SalesDashboardData>(
    `/api/v1/dashboard/sales${params ? `?${params}` : ""}`,
  );
}

export async function getFeedbackDashboard(
  filters: DashboardFilters,
): Promise<FeedbackDashboardData> {
  const params = createSearchParams(filters);
  return fetchJson<FeedbackDashboardData>(
    `/api/v1/dashboard/feedback${params ? `?${params}` : ""}`,
  );
}

export async function askFeedbackRag(
  query: string,
  filters: DashboardFilters,
): Promise<RagResponse> {
  return fetchJson<RagResponse>("/api/v1/rag/query", {
    method: "POST",
    body: JSON.stringify({
      query,
      filters,
    }),
  });
}

export async function getDataPreview(): Promise<DataPreview> {
  return fetchJson<DataPreview>("/api/v1/data/preview");
}
