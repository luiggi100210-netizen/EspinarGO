"""
Endpoints para el servicio de encomiendas.

Crear envío, rastrear por código, asignar conductor,
actualizar estado e historial.

Rutas bajo /api/v1/packages/
"""

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_active_user, get_current_driver
from app.models.package import Package, PackageStatus, PackageTracking
from app.models.user import User
from app.schemas.base import PaginationMeta
from app.schemas.package import (
    PackageListResponse,
    PackagePublic,
    PackageRequest,
    PackageTrackingEvent,
    PackageTrackingResponse,
)
from app.schemas.user import UserPublicOut

router = APIRouter(
    prefix="/packages",
    tags=["Encomiendas"],
)


def generate_tracking_code() -> str:
    """
    Genera un código de seguimiento único.
    Formato: ESP-YYYYMMDD-NNNN
    """
    now = datetime.now(timezone.utc)
    date_part = now.strftime("%Y%m%d")
    number = secrets.randbelow(10000)
    return f"ESP-{date_part}-{number:04d}"


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=PackagePublic,
    summary="Solicitar envío de encomienda",
)
async def create_package(
    data: PackageRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea una nueva encomienda para enviar.
    """
    tracking_code = generate_tracking_code()

    package = Package(
        sender_id=current_user.id,
        tracking_code=tracking_code,
        recipient_name=data.recipient_name,
        recipient_phone=data.recipient_phone,
        delivery_address=data.delivery_address,
        size=data.size,
        description=data.description,
        is_fragile=data.is_fragile,
        payment_method=data.payment_method,
        status=PackageStatus.PENDING,
    )

    db.add(package)
    await db.flush()

    tracking_event = PackageTracking(
        package_id=package.id,
        status=PackageStatus.PENDING,
        description="Encomienda registrada. Buscando conductor...",
    )
    db.add(tracking_event)

    return PackagePublic(
        id=package.id,
        tracking_code=package.tracking_code,
        sender=UserPublicOut.model_validate(package.sender) if package.sender else None,
        driver=UserPublicOut.model_validate(package.driver) if package.driver else None,
        recipient_name=package.recipient_name,
        recipient_phone=package.recipient_phone,
        delivery_address=package.delivery_address,
        size=package.size,
        description=package.description,
        is_fragile=package.is_fragile,
        status=package.status.value,
        price=package.price,
        payment_method=package.payment_method,
        created_at=package.created_at,
        picked_up_at=package.picked_up_at,
        delivered_at=package.delivered_at,
    )


@router.get(
    "/track/{tracking_code}",
    response_model=PackageTrackingResponse,
    summary="Rastrear encomienda por código",
)
async def track_package(
    tracking_code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Rastrea una encomienda por su código de seguimiento.
    Este endpoint es público para que el destinatario pueda rastrear.
    """
    result = await db.execute(
        select(Package).where(Package.tracking_code == tracking_code)
    )
    package = result.scalar_one_or_none()

    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de seguimiento inválido",
        )

    tracking_result = await db.execute(
        select(PackageTracking)
        .where(PackageTracking.package_id == package.id)
        .order_by(PackageTracking.created_at)
    )
    tracking_history = tracking_result.scalars().all()

    tracking_events = [
        PackageTrackingEvent(
            status=event.status.value,
            description=event.description,
            created_at=event.created_at,
        )
        for event in tracking_history
    ]

    return PackageTrackingResponse(
        package=PackagePublic(
            id=package.id,
            tracking_code=package.tracking_code,
            sender=UserPublicOut.model_validate(package.sender) if package.sender else None,
            driver=UserPublicOut.model_validate(package.driver) if package.driver else None,
            recipient_name=package.recipient_name,
            recipient_phone=package.recipient_phone,
            delivery_address=package.delivery_address,
            size=package.size,
            description=package.description,
            is_fragile=package.is_fragile,
            status=package.status.value,
            price=package.price,
            payment_method=package.payment_method,
            created_at=package.created_at,
            picked_up_at=package.picked_up_at,
            delivered_at=package.delivered_at,
        ),
        tracking_history=tracking_events,
    )


@router.get(
    "/my",
    response_model=PackageListResponse,
    summary="Ver mis encomiendas enviadas",
)
async def get_my_packages(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna las encomiendas enviadas por el usuario.
    """
    offset = (page - 1) * per_page

    count_result = await db.execute(
        select(Package).where(Package.sender_id == current_user.id)
    )
    total = len(count_result.scalars().all())

    result = await db.execute(
        select(Package)
        .where(Package.sender_id == current_user.id)
        .order_by(Package.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    packages = result.scalars().all()

    package_list = []
    for pkg in packages:
        package_list.append(
            PackagePublic(
                id=pkg.id,
                tracking_code=pkg.tracking_code,
                sender=UserPublicOut.model_validate(pkg.sender) if pkg.sender else None,
                driver=UserPublicOut.model_validate(pkg.driver) if pkg.driver else None,
                recipient_name=pkg.recipient_name,
                recipient_phone=pkg.recipient_phone,
                delivery_address=pkg.delivery_address,
                size=pkg.size,
                description=pkg.description,
                is_fragile=pkg.is_fragile,
                status=pkg.status.value,
                price=pkg.price,
                payment_method=pkg.payment_method,
                created_at=pkg.created_at,
                picked_up_at=pkg.picked_up_at,
                delivered_at=pkg.delivered_at,
            )
        )

    meta = PaginationMeta.create(total=total, page=page, per_page=per_page)

    return PackageListResponse(packages=package_list, meta=meta)


@router.post(
    "/{package_id}/assign",
    response_model=PackagePublic,
    summary="Asignar encomienda a mi cuenta de conductor",
)
async def assign_package(
    package_id: str,
    current_user: User = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    El conductor se asigna una encomienda pendiente.
    """
    package = await db.get(Package, package_id)

    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encomienda no encontrada",
        )

    if package.status != PackageStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta encomienda ya tiene conductor asignado",
        )

    package.driver_id = current_user.id
    package.status = PackageStatus.ASSIGNED

    tracking_event = PackageTracking(
        package_id=package.id,
        status=PackageStatus.ASSIGNED,
        description="Conductor asignado. En camino a recoger el paquete.",
    )
    db.add(tracking_event)

    return PackagePublic(
        id=package.id,
        tracking_code=package.tracking_code,
        sender=UserPublicOut.model_validate(package.sender) if package.sender else None,
        driver=UserPublicOut.model_validate(package.driver) if package.driver else None,
        recipient_name=package.recipient_name,
        recipient_phone=package.recipient_phone,
        delivery_address=package.delivery_address,
        size=package.size,
        description=package.description,
        is_fragile=package.is_fragile,
        status=package.status.value,
        price=package.price,
        payment_method=package.payment_method,
        created_at=package.created_at,
        picked_up_at=package.picked_up_at,
        delivered_at=package.delivered_at,
    )


@router.post(
    "/{package_id}/update-status",
    response_model=PackagePublic,
    summary="Actualizar estado de la encomienda",
)
async def update_package_status(
    package_id: str,
    status_data: dict,
    current_user: User = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza el estado de la encomienda (conductor).
    Transiciones válidas:
    ASSIGNED → PICKED_UP
    PICKED_UP → IN_TRANSIT
    IN_TRANSIT → DELIVERED
    """
    package = await db.get(Package, package_id)

    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encomienda no encontrada",
        )

    if package.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta encomienda",
        )

    new_status_str = status_data.get("status")
    custom_description = status_data.get("description")

    try:
        new_status = PackageStatus(new_status_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado inválido",
        )

    valid_transitions = {
        PackageStatus.ASSIGNED: [PackageStatus.PICKED_UP],
        PackageStatus.PICKED_UP: [PackageStatus.IN_TRANSIT],
        PackageStatus.IN_TRANSIT: [PackageStatus.DELIVERED],
    }

    if new_status not in valid_transitions.get(package.status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transición no válida. Estados posibles: {', '.join([s.value for s in valid_transitions.get(package.status, [])])}",
        )

    package.status = new_status

    if new_status == PackageStatus.PICKED_UP:
        package.picked_up_at = datetime.now(timezone.utc)
    elif new_status == PackageStatus.DELIVERED:
        package.delivered_at = datetime.now(timezone.utc)

    status_descriptions = {
        PackageStatus.PICKED_UP: "Paquete recogido del remitente",
        PackageStatus.IN_TRANSIT: "Paquete en camino al destino",
        PackageStatus.DELIVERED: "Paquete entregado al destinatario",
    }

    tracking_event = PackageTracking(
        package_id=package.id,
        status=new_status,
        description=custom_description or status_descriptions.get(new_status, "Estado actualizado"),
    )
    db.add(tracking_event)

    return PackagePublic(
        id=package.id,
        tracking_code=package.tracking_code,
        sender=UserPublicOut.model_validate(package.sender) if package.sender else None,
        driver=UserPublicOut.model_validate(package.driver) if package.driver else None,
        recipient_name=package.recipient_name,
        recipient_phone=package.recipient_phone,
        delivery_address=package.delivery_address,
        size=package.size,
        description=package.description,
        is_fragile=package.is_fragile,
        status=package.status.value,
        price=package.price,
        payment_method=package.payment_method,
        created_at=package.created_at,
        picked_up_at=package.picked_up_at,
        delivered_at=package.delivered_at,
    )