"""
Servicio de encomiendas — lógica de negocio del módulo de paquetería.

Crear envío, rastrear por código, asignar conductor,
actualizar estado e historial.

Los endpoints solo orquestan HTTP; toda la lógica vive aquí.
"""

import secrets
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.package import Package, PackageSize, PackageStatus, PackageTracking
from app.models.user import DriverStatus, User, UserRole
from app.schemas.base import PaginationMeta
from app.schemas.package import (
    PackageListResponse,
    PackagePublic,
    PackageRequest,
    PackageTrackingEvent,
    PackageTrackingResponse,
    UpdatePackageStatusRequest,
)
from app.utils.serializers import package_to_public


class PackageService:
    @staticmethod
    def _generate_tracking_code() -> str:
        """Genera un código de seguimiento. Formato: ESP-YYYYMMDD-XXXXXX (16.7M posibilidades/día)."""
        now = datetime.now(timezone.utc)
        date_part = now.strftime("%Y%m%d")
        suffix = secrets.token_hex(3).upper()
        return f"ESP-{date_part}-{suffix}"

    @staticmethod
    async def create_package(
        db: AsyncSession, sender: User, data: PackageRequest
    ) -> PackagePublic:
        tracking_code = PackageService._generate_tracking_code()

        package = Package(
            sender_id=sender.id,
            tracking_code=tracking_code,
            recipient_name=data.recipient_name,
            recipient_phone=data.recipient_phone,
            delivery_address=data.delivery_address,
            size=PackageSize(data.size),
            description=data.description,
            is_fragile=data.is_fragile,
            payment_method=data.payment_method,
            status=PackageStatus.PENDING,
        )
        db.add(package)
        await db.flush()

        db.add(PackageTracking(
            package_id=package.id,
            status=PackageStatus.PENDING,
            description="Encomienda registrada. Buscando conductor...",
        ))
        await db.commit()

        return package_to_public(package)

    @staticmethod
    async def track_package(
        db: AsyncSession, tracking_code: str
    ) -> PackageTrackingResponse:
        package = (
            await db.execute(select(Package).where(Package.tracking_code == tracking_code))
        ).scalar_one_or_none()

        if not package:
            raise ValueError("Código de seguimiento inválido")

        tracking_history = (
            await db.execute(
                select(PackageTracking)
                .where(PackageTracking.package_id == package.id)
                .order_by(PackageTracking.created_at)
            )
        ).scalars().all()

        return PackageTrackingResponse(
            package=package_to_public(package),
            tracking_history=[
                PackageTrackingEvent(
                    status=event.status.value,
                    description=event.description,
                    created_at=event.created_at,
                )
                for event in tracking_history
            ],
        )

    @staticmethod
    async def get_my_packages(
        db: AsyncSession,
        user: User,
        page: int,
        per_page: int,
    ) -> PackageListResponse:
        offset = (page - 1) * per_page

        total = (
            await db.execute(
                select(func.count()).select_from(Package).where(Package.sender_id == user.id)
            )
        ).scalar()

        packages = (
            await db.execute(
                select(Package)
                .where(Package.sender_id == user.id)
                .order_by(Package.created_at.desc())
                .offset(offset)
                .limit(per_page)
            )
        ).scalars().all()

        return PackageListResponse(
            packages=[package_to_public(p) for p in packages],
            meta=PaginationMeta.create(total=total, page=page, per_page=per_page),
        )

    @staticmethod
    async def assign_package(
        db: AsyncSession, package_id: UUID, driver: User
    ) -> PackagePublic:
        if driver.role == UserRole.DRIVER:
            if not driver.driver_profile or driver.driver_profile.driver_status != DriverStatus.APPROVED:
                raise PermissionError("Tu cuenta de conductor no está aprobada para tomar encomiendas")

        package_result = await db.execute(
            select(Package).where(Package.id == package_id).with_for_update()
        )
        package = package_result.scalar_one_or_none()

        if not package:
            raise LookupError("Encomienda no encontrada")
        if package.status != PackageStatus.PENDING:
            raise ValueError("Esta encomienda ya tiene conductor asignado")

        package.driver_id = driver.id
        package.status = PackageStatus.ASSIGNED

        db.add(PackageTracking(
            package_id=package.id,
            status=PackageStatus.ASSIGNED,
            description="Conductor asignado. En camino a recoger el paquete.",
        ))
        await db.commit()

        return package_to_public(package)

    @staticmethod
    async def update_package_status(
        db: AsyncSession,
        package_id: UUID,
        driver: User,
        data: UpdatePackageStatusRequest,
    ) -> PackagePublic:
        package = await db.get(Package, package_id)

        if not package:
            raise LookupError("Encomienda no encontrada")
        if package.driver_id != driver.id:
            raise PermissionError("No tienes acceso a esta encomienda")

        new_status = PackageStatus(data.status)

        valid_transitions: dict[PackageStatus, list[PackageStatus]] = {
            PackageStatus.ASSIGNED: [PackageStatus.PICKED_UP],
            PackageStatus.PICKED_UP: [PackageStatus.IN_TRANSIT],
            PackageStatus.IN_TRANSIT: [PackageStatus.DELIVERED],
        }

        if new_status not in valid_transitions.get(package.status, []):
            valid = ", ".join(s.value for s in valid_transitions.get(package.status, []))
            raise ValueError(f"Transición no válida. Estados posibles: {valid}")

        package.status = new_status

        now = datetime.now(timezone.utc)
        if new_status == PackageStatus.PICKED_UP:
            package.picked_up_at = now
        elif new_status == PackageStatus.DELIVERED:
            package.delivered_at = now

        status_descriptions = {
            PackageStatus.PICKED_UP: "Paquete recogido del remitente",
            PackageStatus.IN_TRANSIT: "Paquete en camino al destino",
            PackageStatus.DELIVERED: "Paquete entregado al destinatario",
        }

        db.add(PackageTracking(
            package_id=package.id,
            status=new_status,
            description=data.description or status_descriptions.get(new_status, "Estado actualizado"),
            updated_by=driver.id,
        ))
        await db.commit()

        return package_to_public(package)

    @staticmethod
    async def get_package(db: AsyncSession, package_id: UUID) -> Package:
        """Retorna el paquete o lanza LookupError si no existe."""
        package = await db.get(Package, package_id)
        if not package:
            raise LookupError("Encomienda no encontrada")
        return package

    @staticmethod
    async def cancel_package(
        db: AsyncSession, package_id: UUID, user: User
    ) -> PackagePublic:
        package = await db.get(Package, package_id)

        if not package:
            raise LookupError("Encomienda no encontrada")

        if package.sender_id != user.id and user.role != UserRole.ADMIN:
            raise PermissionError("No tienes acceso a esta encomienda")

        cancellable = (PackageStatus.PENDING, PackageStatus.ASSIGNED)
        if package.status not in cancellable:
            raise ValueError(
                f"No se puede cancelar una encomienda en estado '{package.status.value}'. "
                "Solo se puede cancelar si está pendiente o asignada."
            )

        package.status = PackageStatus.CANCELLED
        db.add(PackageTracking(
            package_id=package.id,
            status=PackageStatus.CANCELLED,
            description="Envío cancelado por el remitente",
            updated_by=user.id,
        ))
        await db.commit()

        return package_to_public(package)

    @staticmethod
    async def get_driver_packages(
        db: AsyncSession,
        driver: User,
        page: int,
        per_page: int,
    ) -> PackageListResponse:
        """Encomiendas activas asignadas al conductor (ASSIGNED, PICKED_UP, IN_TRANSIT)."""
        active_statuses = [
            PackageStatus.ASSIGNED,
            PackageStatus.PICKED_UP,
            PackageStatus.IN_TRANSIT,
        ]

        total = (
            await db.execute(
                select(func.count())
                .select_from(Package)
                .where(
                    Package.driver_id == driver.id,
                    Package.status.in_(active_statuses),
                )
            )
        ).scalar()

        packages = (
            await db.execute(
                select(Package)
                .where(
                    Package.driver_id == driver.id,
                    Package.status.in_(active_statuses),
                )
                .order_by(Package.created_at.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
        ).scalars().all()

        return PackageListResponse(
            packages=[package_to_public(p) for p in packages],
            meta=PaginationMeta.create(total=total, page=page, per_page=per_page),
        )
