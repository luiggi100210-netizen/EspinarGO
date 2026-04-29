import { api } from './api';
import type { User, DriverProfile, PaginatedResponse } from '@/types';

interface UserFilters {
  role?: string;
  status?: string;
  search?: string;
}

interface UsersResponse {
  users: User[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

interface DriversResponse {
  drivers: DriverProfile[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

/**
 * Servicio de gestión de usuarios y conductores
 */

export async function getUsers(
  page = 1,
  perPage = 20,
  filters: UserFilters = {}
): Promise<UsersResponse> {
  const params = new URLSearchParams();
  params.append('page', String(page));
  params.append('per_page', String(perPage));

  if (filters.role) params.append('role', filters.role);
  if (filters.status) params.append('status', filters.status);
  if (filters.search) params.append('search', filters.search);

  const response = await api.get<UsersResponse>(`/api/v1/users?${params}`);
  return response.data;
}

export async function getUserById(id: string): Promise<User> {
  const response = await api.get<User>(`/api/v1/users/${id}`);
  return response.data;
}

export async function suspendUser(id: string, reason: string): Promise<User> {
  const response = await api.patch<User>(`/api/v1/users/${id}/suspend`, { reason });
  return response.data;
}

export async function activateUser(id: string): Promise<User> {
  const response = await api.patch<User>(`/api/v1/users/${id}/activate`);
  return response.data;
}

export async function getDriverProfile(userId: string): Promise<DriverProfile> {
  const response = await api.get<DriverProfile>(`/api/v1/users/drivers/${userId}`);
  return response.data;
}

export async function approveDriver(userId: string): Promise<DriverProfile> {
  const response = await api.post<DriverProfile>(`/api/v1/users/drivers/${userId}/approve`);
  return response.data;
}

export async function rejectDriver(userId: string, reason: string): Promise<DriverProfile> {
  const response = await api.post<DriverProfile>(`/api/v1/users/drivers/${userId}/reject`, { reason });
  return response.data;
}

export async function getPendingDrivers(page = 1, perPage = 20): Promise<DriversResponse> {
  const params = new URLSearchParams();
  params.append('page', String(page));
  params.append('per_page', String(perPage));
  params.append('status', 'under_review');

  const response = await api.get<DriversResponse>(`/api/v1/users/drivers?${params}`);
  return response.data;
}

export async function getAllDrivers(
  page = 1,
  perPage = 20,
  status?: string
): Promise<DriversResponse> {
  const params = new URLSearchParams();
  params.append('page', String(page));
  params.append('per_page', String(perPage));
  if (status) params.append('status', status);

  const response = await api.get<DriversResponse>(`/api/v1/users/drivers?${params}`);
  return response.data;
}