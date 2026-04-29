import { api, setAuthTokens, clearAuthTokens } from './api';
import type { TokenResponse, User } from '@/types';

/**
 * Servicio de autenticación para EspinarGo Admin
 */

export async function login(phone: string, password: string): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>('/api/v1/auth/login', {
    phone_number: phone,
    password,
  });

  const { access_token, refresh_token, user } = response.data;
  setAuthTokens(access_token, refresh_token);
  localStorage.setItem('user', JSON.stringify(user));

  return response.data;
}

export async function logout(refreshToken: string): Promise<void> {
  try {
    await api.post('/api/v1/auth/logout', {
      refresh_token: refreshToken,
    });
  } finally {
    clearAuthTokens();
    localStorage.removeItem('user');
  }
}

export async function getMyProfile(): Promise<User> {
  const response = await api.get<User>('/api/v1/auth/me');
  return response.data;
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  const refreshToken = localStorage.getItem('refresh_token');
  
  await api.post('/api/v1/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  });

  if (refreshToken) {
    await logout(refreshToken);
  }
}