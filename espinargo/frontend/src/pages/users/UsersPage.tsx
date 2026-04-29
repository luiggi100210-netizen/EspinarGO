import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getUsers, suspendUser, activateUser } from '@/services/users.service';
import { DataTable } from '@/components/common/DataTable';
import { StatusBadge } from '@/components/common/StatusBadge';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { User, Check, X } from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

export function UsersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [role, setRole] = useState('');
  const [status, setStatus] = useState('');
  const [suspendDialog, setSuspendDialog] = useState<{ open: boolean; userId: string | null }>({
    open: false,
    userId: null,
  });

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['users', page, search, role, status],
    queryFn: () => getUsers(page, 20, { search, role, status }),
  });

  const handleToggleUser = async (userId: string, currentStatus: string) => {
    try {
      if (currentStatus === 'active') {
        await suspendUser(userId, 'Suspendido por administrador');
      } else {
        await activateUser(userId);
      }
      refetch();
    } catch (error) {
      console.error('Error:', error);
    }
    setSuspendDialog({ open: false, userId: null });
  };

  const columns = [
    {
      key: 'user',
      header: 'Usuario',
      render: (row: { id: string; full_name: string; phone_number: string }) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center text-white font-medium">
            {row.full_name.charAt(0)}
          </div>
          <div>
            <p className="font-medium text-gray-900">{row.full_name}</p>
            <p className="text-sm text-gray-500">{row.phone_number}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'role',
      header: 'Rol',
      render: (row: { role: string }) => (
        <span className="capitalize">{row.role}</span>
      ),
    },
    {
      key: 'status',
      header: 'Estado',
      render: (row: { status: string }) => (
        <StatusBadge status={row.status} type="user" />
      ),
    },
    {
      key: 'phone_verified',
      header: 'Teléfono',
      render: (row: { phone_verified: boolean }) => (
        row.phone_verified ? (
          <Check className="w-5 h-5 text-green-600" />
        ) : (
          <X className="w-5 h-5 text-red-600" />
        )
      ),
    },
    {
      key: 'created_at',
      header: 'Registro',
      render: (row: { created_at: string }) => (
        <span className="text-sm text-gray-500">
          {format(new Date(row.created_at), 'dd MMM yyyy', { locale: es })}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Acciones',
      render: (row: { id: string; status: string }) => (
        <button
          onClick={() => handleToggleUser(row.id, row.status)}
          className={`px-3 py-1 text-sm rounded-lg ${
            row.status === 'active'
              ? 'bg-red-100 text-red-700 hover:bg-red-200'
              : 'bg-green-100 text-green-700 hover:bg-green-200'
          }`}
        >
          {row.status === 'active' ? 'Suspender' : 'Activar'}
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Usuarios</h1>
          <p className="text-gray-500">{data?.total ?? 0} usuarios registrados</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-4">
        <select
          value={role}
          onChange={(e) => { setRole(e.target.value); setPage(1); }}
          className="input w-auto"
        >
          <option value="">Todos los roles</option>
          <option value="passenger">Pasajero</option>
          <option value="driver">Conductor</option>
          <option value="admin">Admin</option>
        </select>

        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="input w-auto"
        >
          <option value="">Todos los estados</option>
          <option value="active">Activo</option>
          <option value="pending">Pendiente</option>
          <option value="suspended">Suspendido</option>
          <option value="banned">Bloqueado</option>
        </select>
      </div>

      <DataTable
        columns={columns}
        data={data?.users ?? []}
        isLoading={isLoading}
        onSearch={setSearch}
        searchPlaceholder="Buscar por nombre o teléfono..."
        pagination={
          data ? {
            page,
            total_pages: data.total_pages,
            onPageChange: setPage,
          } : undefined
        }
      />

      <ConfirmDialog
        isOpen={suspendDialog.open}
        title="Suspender usuario"
        message="¿Estás seguro de que deseas suspender este usuario? Ya no podrá acceder a la aplicación."
        confirmText="Suspender"
        confirmVariant="danger"
        onConfirm={() => suspendDialog.userId && handleToggleUser(suspendDialog.userId, 'active')}
        onCancel={() => setSuspendDialog({ open: false, userId: null })}
      />
    </div>
  );
}