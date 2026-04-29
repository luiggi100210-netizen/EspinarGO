import { clsx } from 'clsx';

type StatusType = 'user' | 'driver' | 'trip' | 'package';

interface StatusBadgeProps {
  status: string;
  type: StatusType;
}

const statusLabels: Record<string, Record<string, { label: string; className: string }>> = {
  user: {
    active: { label: 'Activo', className: 'bg-green-100 text-green-700' },
    pending: { label: 'Pendiente', className: 'bg-yellow-100 text-yellow-700' },
    suspended: { label: 'Suspendido', className: 'bg-orange-100 text-orange-700' },
    banned: { label: 'Bloqueado', className: 'bg-red-100 text-red-700' },
  },
  driver: {
    approved: { label: 'Aprobado', className: 'bg-green-100 text-green-700' },
    under_review: { label: 'En revisión', className: 'bg-blue-100 text-blue-700' },
    pending_docs: { label: 'Pendiente docs', className: 'bg-yellow-100 text-yellow-700' },
    rejected: { label: 'Rechazado', className: 'bg-red-100 text-red-700' },
    suspended: { label: 'Suspendido', className: 'bg-orange-100 text-orange-700' },
  },
  trip: {
    completed: { label: 'Completado', className: 'bg-green-100 text-green-700' },
    in_progress: { label: 'En curso', className: 'bg-blue-100 text-blue-700' },
    accepted: { label: 'Aceptado', className: 'bg-cyan-100 text-cyan-700' },
    searching: { label: 'Buscando', className: 'bg-yellow-100 text-yellow-700' },
    cancelled: { label: 'Cancelado', className: 'bg-red-100 text-red-700' },
    negotiating: { label: 'Negociando', className: 'bg-purple-100 text-purple-700' },
  },
  package: {
    delivered: { label: 'Entregado', className: 'bg-green-100 text-green-700' },
    in_transit: { label: 'En tránsito', className: 'bg-blue-100 text-blue-700' },
    picked_up: { label: 'Recogido', className: 'bg-cyan-100 text-cyan-700' },
    assigned: { label: 'Asignado', className: 'bg-yellow-100 text-yellow-700' },
    pending: { label: 'Pendiente', className: 'bg-gray-100 text-gray-700' },
    cancelled: { label: 'Cancelado', className: 'bg-red-100 text-red-700' },
  },
};

export function StatusBadge({ status, type }: StatusBadgeProps) {
  const statusInfo = statusLabels[type]?.[status];

  if (!statusInfo) {
    return (
      <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-700">
        {status}
      </span>
    );
  }

  return (
    <span className={clsx('px-2 py-1 text-xs font-medium rounded-full', statusInfo.className)}>
      {statusInfo.label}
    </span>
  );
}