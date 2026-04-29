import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Menu, User, LogOut, Settings } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { clsx } from 'clsx';

interface HeaderProps {
  onMenuClick: () => void;
}

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/users': 'Usuarios',
  '/drivers': 'Conductores',
  '/trips': 'Viajes',
  '/packages': 'Encomiendas',
  '/settings': 'Configuración',
};

export function Header({ onMenuClick }: HeaderProps) {
  const location = useLocation();
  const { user, logout } = useAuth();
  const [showMenu, setShowMenu] = useState(false);

  const title = pageTitles[location.pathname] || 'EspinarGo';

  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
        >
          <Menu className="w-6 h-6" />
        </button>
        <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
      </div>

      <div className="relative">
        <button
          onClick={() => setShowMenu(!showMenu)}
          className="flex items-center gap-3 p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
        >
          <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white text-sm font-medium">
            {user?.full_name?.charAt(0) || 'A'}
          </div>
        </button>

        {showMenu && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setShowMenu(false)}
            />
            <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-100 py-2 z-20">
              <div className="px-4 py-2 border-b border-gray-100">
                <p className="font-medium text-gray-900">{user?.full_name}</p>
                <p className="text-sm text-gray-500">{user?.email}</p>
              </div>
              <button className="flex items-center gap-3 px-4 py-2 w-full text-left text-gray-700 hover:bg-gray-50">
                <User className="w-4 h-4" />
                Mi perfil
              </button>
              <button className="flex items-center gap-3 px-4 py-2 w-full text-left text-gray-700 hover:bg-gray-50">
                <Settings className="w-4 h-4" />
                Configuración
              </button>
              <hr className="my-2 border-gray-100" />
              <button
                onClick={logout}
                className="flex items-center gap-3 px-4 py-2 w-full text-left text-red-600 hover:bg-red-50"
              >
                <LogOut className="w-4 h-4" />
                Cerrar sesión
              </button>
            </div>
          </>
        )}
      </div>
    </header>
  );
}