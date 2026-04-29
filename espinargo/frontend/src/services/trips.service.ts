import { api } from './api';
import type { Trip, PaginatedResponse } from '@/types';

interface TripFilters {
  status?: string;
  date_from?: string;
  date_to?: string;
  passenger_id?: string;
}

interface TripsResponse {
  trips: Trip[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

interface TripStats {
  total: number;
  by_status: Record<string, number>;
  today_count: number;
  today_revenue: number;
  month_revenue: number;
}

/**
 * Servicio de gestión de viajes
 */

export async function getTrips(
  page = 1,
  perPage = 20,
  filters: TripFilters = {}
): Promise<TripsResponse> {
  const params = new URLSearchParams();
  params.append('page', String(page));
  params.append('per_page', String(perPage));

  if (filters.status) params.append('status', filters.status);
  if (filters.date_from) params.append('date_from', filters.date_from);
  if (filters.date_to) params.append('date_to', filters.date_to);
  if (filters.passenger_id) params.append('passenger_id', filters.passenger_id);

  const response = await api.get<TripsResponse>(`/api/v1/trips/admin?${params}`);
  return response.data;
}

export async function getTripById(id: string): Promise<Trip> {
  const response = await api.get<Trip>(`/api/v1/trips/${id}`);
  return response.data;
}

export async function getTripStats(): Promise<TripStats> {
  const response = await api.get<TripStats>('/api/v1/trips/admin/stats');
  return response.data;
}

export async function getActiveTrips(): Promise<Trip[]> {
  const response = await api.get<{ trips: Trip[] }>('/api/v1/trips/active');
  return response.data.trips;
}