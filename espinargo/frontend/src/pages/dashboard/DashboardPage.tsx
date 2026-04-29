import { Users, Car, MapPin, Package, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { StatsCard } from '@/components/common/StatsCard';
import { useStats } from '@/hooks/useStats';

const weeklyData = [
  { day: 'Lun', trips: 45 },
  { day: 'Mar', trips: 52 },
  { day: 'Mié', trips: 38 },
  { day: 'Jue', trips: 65 },
  { day: 'Vie', trips: 78 },
  { day: 'Sáb', trips: 92 },
  { day: 'Dom', trips: 58 },
];

export function DashboardPage() {
  const { stats, isLoading } = useStats();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500">Resumen del negocio</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total Usuarios"
          value={stats?.total_users ?? 0}
          icon={Users}
          color="orange"
          isLoading={isLoading}
        />
        <StatsCard
          title="Conductores Activos"
          value={stats?.total_drivers ?? 0}
          icon={Car}
          color="green"
          isLoading={isLoading}
        />
        <StatsCard
          title="Viajes Hoy"
          value={stats?.total_trips ?? 0}
          icon={MapPin}
          color="blue"
          isLoading={isLoading}
        />
        <StatsCard
          title="Encomiendas Hoy"
          value={stats?.total_packages ?? 0}
          icon={Package}
          color="purple"
          isLoading={isLoading}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Conductores Pendientes</h3>
            <span className="bg-red-100 text-red-600 px-3 py-1 rounded-full text-sm font-medium">
              {stats?.pending_drivers ?? 0}
            </span>
          </div>
          <p className="text-sm text-gray-500 mb-4">
            Conductores esperando aprobación de documentos
          </p>
          <a
            href="/drivers?filter=pending"
            className="text-primary hover:underline text-sm font-medium"
          >
            Revisar ahora →
          </a>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Viajes Activos</h3>
            <span className="bg-blue-100 text-blue-600 px-3 py-1 rounded-full text-sm font-medium">
              {stats?.active_trips ?? 0}
            </span>
          </div>
          <p className="text-sm text-gray-500 mb-4">
            Viajes en curso en este momento
          </p>
          <a
            href="/trips?filter=active"
            className="text-primary hover:underline text-sm font-medium"
          >
            Ver en vivo →
          </a>
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">
          Viajes por día - Última semana
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={weeklyData}>
              <XAxis dataKey="day" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="trips" fill="#E8521A" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Últimos Viajes</h3>
          <div className="space-y-3">
            {[
              { route: 'Plaza de Armas → San Felipe', price: 'S/8.00', status: 'completed' },
              { route: 'Mercado → CC. El Polo', price: 'S/12.00', status: 'in_progress' },
              { route: 'Estación → Plaza de Armas', price: 'S/5.00', status: 'completed' },
            ].map((trip, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span className="text-gray-700">{trip.route}</span>
                <span className="text-gray-500">{trip.price}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Últimas Encomiendas</h3>
          <div className="space-y-3">
            {[
              { code: 'ESP-20240420-0042', status: 'in_transit' },
              { code: 'ESP-20240420-0041', status: 'delivered' },
              { code: 'ESP-20240420-0040', status: 'pending' },
            ].map((pkg, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span className="font-mono text-gray-700">{pkg.code}</span>
                <span className="text-gray-500">{pkg.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}