import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getTrips } from '@/services/trips.service';
import { DataTable } from '@/components/common/DataTable';
import { StatusBadge } from '@/components/common/StatusBadge';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

export function TripsPage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['trips', page, status],
    queryFn: () => getTrips(page, 20, { status: status || undefined }),
  });

  const columns = [
    {
      key: 'passenger',
      header: 'Pasajero',
      render: (row: { passenger: { full_name: string } }) => (
        <span className="font-medium">{row.passenger?.full_name || 'Sin asignar'}</span>
      ),
    },
    {
      key: 'driver',
      header: 'Conductor',
      render: (row: { driver: { full_name: string } }) => (
        <span className="text-gray-500">{row.driver?.full_name || 'Sin asignar'}</span>
      ),
    },
    {
      key: 'route',
      header: 'Ruta',
      render: (row: { origin_address: string; dest_address: string }) => (
        <div className="max-w-xs">
          <p className="truncate text-sm">{row.origin_address}</p>
          <p className="truncate text-sm text-gray-500">→ {row.dest_address}</p>
        </div>
      ),
    },
    {
      key: 'price',
      header: 'Precio',
      render: (row: { proposed_price: string; final_price: string }) => (
        <div>
          <span className="text-gray-400 line-through text-sm">S/{row.proposed_price}</span>
          {row.final_price && (
            <span className="ml-2 font-medium text-green-600">S/{row.final_price}</span>
          )}
        </div>
      ),
    },
    {
      key: 'payment',
      header: 'Pago',
      render: (row: { payment_method: string }) => (
        <span className="capitalize text-sm">{row.payment_method}</span>
      ),
    },
    {
      key: 'status',
      header: 'Estado',
      render: (row: { status: string }) => (
        <StatusBadge status={row.status} type="trip" />
      ),
    },
    {
      key: 'created_at',
      header: 'Fecha',
      render: (row: { created_at: string }) => (
        <span className="text-sm text-gray-500">
          {format(new Date(row.created_at), 'dd MMM HH:mm', { locale: es })}
        </span>
      ),
    },
  ];

  const statusOptions = [
    { value: '', label: 'Todos los estados' },
    { value: 'searching', label: 'Buscando' },
    { value: 'negotiating', label: 'Negociando' },
    { value: 'accepted', label: 'Aceptado' },
    { value: 'in_progress', label: 'En curso' },
    { value: 'completed', label: 'Completado' },
    { value: 'cancelled', label: 'Cancelado' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Viajes</h1>
        <p className="text-gray-500">Monitorea todos los viajes</p>
      </div>

      <div className="flex gap-4">
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="input w-auto"
        >
          {statusOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      <DataTable
        columns={columns}
        data={data?.trips ?? []}
        isLoading={isLoading}
        emptyMessage="No hay viajes"
        pagination={
          data ? {
            page,
            total_pages: data.total_pages,
            onPageChange: setPage,
          } : undefined
        }
      />
    </div>
  );
}