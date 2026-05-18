"""
Servicio de notificaciones push vía Firebase Cloud Messaging (FCM).

Solo se inicializa si FIREBASE_CREDENTIALS_JSON está configurado.
Falla silenciosamente si no está disponible, para no romper el flujo
en entornos sin Firebase configurado.
"""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_firebase_app = None


def _get_firebase_app():
    """Lazy init del app de Firebase. Retorna None si no está configurado."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    try:
        from app.core.config import settings
        if not settings.FIREBASE_CREDENTIALS_JSON:
            return None

        import firebase_admin
        from firebase_admin import credentials

        cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
        cred = credentials.Certificate(cred_dict)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK inicializado")
        return _firebase_app
    except Exception:
        logger.exception("No se pudo inicializar Firebase Admin SDK")
        return None


async def send_push(
    device_token: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> bool:
    """
    Envía una notificación push a un dispositivo específico.

    Returns:
        bool: True si se envió, False si falló o Firebase no está configurado.
    """
    app = _get_firebase_app()
    if not app:
        return False

    try:
        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=device_token,
            android=messaging.AndroidConfig(priority="high"),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(sound="default")
                )
            ),
        )
        messaging.send(message, app=app)
        return True
    except Exception:
        logger.exception("Error enviando push a token %s", device_token[:20])
        return False


async def send_push_to_many(
    device_tokens: list[str],
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> None:
    """Envía push a múltiples tokens. Ignora tokens inválidos."""
    if not device_tokens:
        return

    app = _get_firebase_app()
    if not app:
        return

    try:
        from firebase_admin import messaging

        messages = [
            messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                token=token,
                android=messaging.AndroidConfig(priority="high"),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound="default")
                    )
                ),
            )
            for token in device_tokens
        ]
        batch_response = messaging.send_each(messages, app=app)
        failed = sum(1 for r in batch_response.responses if not r.success)
        if failed:
            logger.warning("Push: %d/%d fallaron", failed, len(device_tokens))
    except Exception:
        logger.exception("Error en send_push_to_many")
