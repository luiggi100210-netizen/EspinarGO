import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAllDrivers, approveDriver, rejectDriver } from '@/services/users.service';
import { DataTable } from '@/components/common/DataTable';
import { StatusBadge } from '@/components/common/StatusBadge';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { Car, Star, FileText } from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

type TabType = 'pending' | 'approved' | 'rejected' | 'all';

export function DriversPage() {
  const [page, setPage] = useState(1);
  const [tab, setTab] = useState<TabType>('pending');
  const [selectedDriver, setSelectedDriver] = useState<string | null>(null);
  const [rejectDialog, setRejectDialog] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const queryClient = useQueryClient();

  const statusMap: Record<TabType, string | undefined> = {
    pending: 'under_review',
    approved: 'approved',
    rejected: 'rejected',
    all: undefined,
  };

  const { data, isLoading } = useQuery({
    queryKey: ['drivers', page, statusMap[tab]],
    queryFn: () => getAllDrivers(page, 20, statusMap[tab]),
  });

  const approveMutation = useMutation({
    mutationFn: approveDriver,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drivers'] });
      setSelectedDriver(null);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ userId, reason }: { userId: string; reason: string }) =>
      rejectDriver(userId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drivers'] });
      setRejectDialog(false);
      setSelectedDriver(null);
      setRejectReason('');
    },
  });

  const handleApprove = (userId: string) => {
    approveMutation.mutate(userId);
  };

  const handleReject = () => {
    if (selectedDriver && rejectReason) {
      rejectMutation.mutate({ userId: selectedDriver, reason: rejectReason });
    }
  };

  const pendingCount = data?.total ?? 0;

  const columns = [
    {
      key: 'driver',
      header: 'Conductor',
      render: (row: { user: { full_name: string; phone_number: string } }) => (
        <div>
          <p className="font-medium text-gray-900">{row.user.full_name}</p>
          <p className="text-sm text-gray-500">{row.user.phone_number}</p>
        </div>
      ),
    },
    {
      key: 'vehicle',
      header: 'Vehículo',
      render: (row: { vehicle_type: string; vehicle_plate: string }) => (
        <div className="flex items-center gap-2">
          <Car className="w-4 h-4 text-gray-400" />
          <span className="capitalize">{row.vehicle_type || '-'}</span>
          <span className="font-mono text-sm">{row.vehicle_plate || ''}</span>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Estado',
      render: (row: { driver_status: string }) => (
        <StatusBadge status={row.driver_status} type="driver" />
      ),
    },
    {
      key: 'rating',
      header: 'Calificación',
      render: (row: { rating_display: number; total_trips: number }) => (
        <div className="flex items-center gap-1">
          <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
          <span>{row.rating_display.toFixed(1)}</span>
          <span className="text-gray-400 text-sm">({row.total_trips})</span>
        </div>
      ),
    },
    {
      key: 'created_at',
      header: 'Fecha',
      render: (row: { approved_at: string }) => (
        <span className="text-sm text-gray-500">
          {row.approved_at
            ? format(new Date(row.approved_at), 'dd MMM yyyy', { locale: es })
            : '-'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Acciones',
      render: (row: { user_id: string; driver_status: string }) => (
        <div className="flex gap-2">
          <button
            onClick={() => setSelectedDriver(row.user_id)}
            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
            title="Ver documentos"
          >
            <FileText className="w-4 h-4" />
          </button>
          {row.driver_status === 'under_review' && (
            <>
              <button
                onClick={() => handleApprove(row.user_id)}
                className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200"
              >
                Aprobar
              </button>
              <button
                onClick={() => {
                  setSelectedDriver(row.user_id);
                  setRejectDialog(true);
                }}
                className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
              >
                Rechazar
              </button>
            </>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Conductores</h1>
        <p className="text-gray-500">Gestiona la aprobación de conductores</p>
      </div>

      <div className="flex gap-2 border-b border-gray-200">
        {[
          { key: 'pending', label: 'Pendientes de aprobación', badge: tab === 'pending' ? pendingCount : 0 },
          { key: 'approved', label: 'Aprobados' },
          { key: 'rejected', label: 'Rechazados' },
          { key: 'all', label: 'Todos' },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => { setTab(t.key as TabType); setPage(1); }}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
              tab === t.key
                ? 'border-primary text-primary'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
            {t.badge !== undefined && t.badge > 0 && (
              <span className="ml-2 bg-red-500 text-white px-2 py-0.5 rounded-full text-xs">
                {t.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      <DataTable
        columns={columns}
        data={data?.drivers ?? []}
        isLoading={isLoading}
        emptyMessage="No hay conductores"
      />

      <ConfirmDialog
        isOpen={rejectDialog}
        title="Rechazar conductor"
        message="¿Estás seguro de que deseas rechazar este conductor? Especifica el motivo:"
        confirmText="Rechazar"
        confirmVariant="danger"
        onConfirm={handleReject}
        onCancel={() => { setRejectDialog(false); setRejectReason(''); }}
      >
        <textarea
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          placeholder="Motivo del rechazo..."
          className="input mt-4"
          rows={3}
        />
      </ConfirmDialog>
    </div>
  );
}