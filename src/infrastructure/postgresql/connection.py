from typing import ClassVar

import asyncpg


class PostgreSQLConnection:
    """Pool de conexiones singleton a PostgreSQL, compartido por todos los repositorios."""

    _pool: ClassVar[asyncpg.Pool | None] = None

    @classmethod
    async def get_pool(cls, dsn: str) -> asyncpg.Pool:
        """Devuelve el pool de conexiones, creándolo la primera vez.

        Args:
            dsn: cadena de conexión (`DATABASE_URL`).

        Returns:
            Pool de conexiones asyncpg.
        """
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(dsn=dsn)
        return cls._pool

    @classmethod
    async def close(cls) -> None:
        """Cierra el pool de conexiones, si existe. Se llama al apagar el proceso."""
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None
