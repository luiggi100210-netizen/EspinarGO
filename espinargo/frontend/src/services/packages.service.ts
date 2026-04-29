import { api } from './api';
import type { Package } from '@/types';

interface PackageFilters {
  status?: string;
  date_from?: string;
  date_to?: string;
}

interface PackagesResponse {
  packages: Package[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

interface PackageTrackingEvent {
  status: string;
  description: string;
  created_at: string;
}

interface PackageTrackingResponse {
  package: Package;
  tracking_history: PackageTrackingEvent[];
}

interface PackageStats {
  total: number;
  by_status: Record<string, number>;
  today_count: number;
  today_revenue: number;
}

/**
 * Servicio de gestión de encomiendas
 */

export async function getPackages(
  page = 1,
  perPage = 20,
  filters: PackageFilters = {}
): Promise<PackagesResponse> {
  const params = new URLSearchParams();
  params.append('page', String(page));
  params.append('per_page', String(perPage));

  if (filters.status) params.append('status', filters.status);
  if (filters.date_from) params.append('date_from', filters.date_from);
  if (filters.date_to) params.append('date_to', filters.date_to);

  const response = await api.get<PackagesResponse>(`/api/v1/packages?${params}`);
  return response.data;
}

export async function trackPackage(code: string): Promise<PackageTrackingResponse> {
  const response = await api.get<PackageTrackingResponse>(`/api/v1/packages/track/${code}`);
  return response.data;
}

export async function getPackageStats(): Promise<PackageStats> {
  const response = await api.get<PackageStats>('/api/v1/packages/admin/stats');
  return response.data;
}