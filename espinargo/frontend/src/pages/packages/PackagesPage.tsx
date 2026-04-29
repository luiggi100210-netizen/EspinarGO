import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getPackages, trackPackage } from '@/services/packages.service';
import { DataTable } from '@/components/common/DataTable';
import { StatusBadge } from '@/components/common/StatusBadge';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { Search } from 'lucide-react';

export function PackagesPage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');
  const [trackingCode, setTrackingCode] = useState('');
  const [showTracking, setShowTracking] = useState(false);
  const [trackingData, setTrackingData] = useState<unknown>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['packages', page, status],
    queryFn: () => getPackages(page, 20, { status: status || undefined }),
  });

  const handleTrack = async () => {
    if (trackingCode) {
      try {
        const result = await trackPackage(trackingCode);
        setTrackingData(result);
        setShowTracking(true);
      } catch (error) {
        alert('Código de seguimiento no encontrado');
      }
    }
  };

  const columns = [
    {
      key: 'tracking_code',
      header: 'Código',
      render: (row: { tracking_code: string }) => (
        <span className="font-mono text-sm">{row.tracking_code}</span>
      ),
    },
    {
      key: 'sender',
      header: 'Remitente',
      render: (row: { sender: { full_name: string } }) => (
        <span>{row.sender?.full_name || '-'}</span>
      ),
    },
    {
      key: 'recipient',
      header: 'Destinatario',
      render: (row: { recipient_name: string; recipient_phone: string }) => (
        <div>
          <p className="font-medium">{row.recipient_name}</p>
          <p className="text-sm text-gray-500">{row.recipient_phone}</p>
        </div>
      ),
    },
    {
      key: 'size',
      header: 'Tamaño',
      render: (row: { size: string }) => (
        <span className="capitalize">{row.size}</span>
      ),
    },
    {
      key: 'status',
      header: 'Estado',
      render: (row: { status: string }) => (
        <StatusBadge status={row.status} type="package" />
      ),
    },
    {
      key: 'price',
      header: 'Precio',
      render: (row: { price: string }) => (
        <span>S/{row.price || '0.00'}</span>
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
    { value: 'pending', label: 'Pendiente' },
    { value: 'assigned', label: 'Asignado' },
    { value: 'picked_up', label: 'Recogido' },
    { value: 'in_transit', label: 'En tránsito' },
    { value: 'delivered', label: 'Entregado' },
    { value: 'cancelled', label: 'Cancelado' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Encomiendas</h1>
        <p className="text-gray-500">Monitorea los envíos</p>
      </div>

      <div className="card">
        <h3 className="font-medium text-gray-900 mb-3">Rastrear encomienda</h3>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={trackingCode}
              onChange={(e) => setTrackingCode(e.target.value)}
              placeholder="ESP-20240420-0042"
              className="input pl-10 font-mono"
            />
          </div>
          <button onClick={handleTrack} className="btn-primary">
            Rastrear
          </button>
        </div>

        {showTracking && trackingData && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <pre className="text-sm overflow-auto">
              {JSON.stringify(trackingData, null, 2)}
            </pre>
            <button
              onClick={() => setShowTracking(false)}
              className="mt-2 text-sm text-gray-500 hover:text-gray-700"
            >
              Cerrar
            </button>
          </div>
        )}
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
        data={data?.packages ?? []}
        isLoading={isLoading}
        emptyMessage="No hay encomiendas"
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