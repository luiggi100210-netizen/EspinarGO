import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/auth.store';
import { login as loginService, logout as logoutService } from '@/services/auth.service';

/**
 * Hook para manejar la autenticación en componentes
 */
export function useAuth() {
  const navigate = useNavigate();
  const { user, isAuthenticated, isLoading, setUser, logout: storeLogout, setLoading } = useAuthStore();
  const [error, setError] = useState<string | null>(null);

  const login = async (phone: string, password: string) => {
    setError(null);
    setLoading(true);

    try {
      const response = await loginService(phone, password);
      setUser(response.user);
      navigate('/');
      return true;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al iniciar sesión';
      setError(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      try {
        await logoutService(refreshToken);
      } catch {
        // Ignorar errores en logout
      }
    }
    storeLogout();
    navigate('/login');
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
  };
}