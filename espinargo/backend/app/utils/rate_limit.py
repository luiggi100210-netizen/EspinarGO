"""
Rate limiting genérico usando Redis.

Centraliza la lógica de rate limiting para endpoints de auth.
Usa el mismo cliente Redis que otp_service para evitar duplicación.
"""

from app.services.otp_service import get_redis

LOGIN_MAX = 10
LOGIN_WINDOW = 900  # 15 minutos

REGISTER_MAX = 5
REGISTER_WINDOW = 3600  # 1 hora


async def _check_rate(key: str, max_attempts: int, window: int) -> tuple[bool, int]:
    redis = await get_redis()
    current = await redis.get(key)

    if current and int(current) >= max_attempts:
        ttl = await redis.ttl(key)
        return False, max(ttl, 0)

    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, window)
    await pipe.execute()

    return True, 0


async def check_login_rate_limit(ip: str) -> tuple[bool, int]:
    return await _check_rate(f"login_rate:{ip}", LOGIN_MAX, LOGIN_WINDOW)


async def check_register_rate_limit(ip: str) -> tuple[bool, int]:
    return await _check_rate(f"register_rate:{ip}", REGISTER_MAX, REGISTER_WINDOW)
