from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import asyncpg

from src.infrastructure.postgresql.connection import PostgreSQLConnection
from src.infrastructure.postgresql.postgresql_base_exception import PostgreSQLBaseException


class PostgreSQLBaseRepository:
    """Base de los repositorios PostgreSQL: ejecuta consultas sobre el pool compartido."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    async def execute_query(self, query: str, *args: Any) -> list[asyncpg.Record]:
        """Ejecuta una consulta de lectura y devuelve todas las filas.

        Args:
            query: sentencia SQL parametrizada (`$1`, `$2`, …).
            args: valores de los parámetros.

        Returns:
            Filas devueltas por la consulta.

        Raises:
            PostgreSQLBaseException: error al ejecutar la consulta.
        """
        try:
            pool = await PostgreSQLConnection.get_pool(self._dsn)
            async with pool.acquire() as connection:
                rows: list[asyncpg.Record] = await connection.fetch(query, *args)
                return rows
        except asyncpg.PostgresError as e:
            raise PostgreSQLBaseException(f"Error al consultar PostgreSQL: {e}") from None

    async def execute_update(self, query: str, *args: Any) -> str:
        """Ejecuta una sentencia de escritura (INSERT/UPDATE/DELETE).

        Args:
            query: sentencia SQL parametrizada (`$1`, `$2`, …).
            args: valores de los parámetros.

        Returns:
            Etiqueta de estado devuelta por PostgreSQL (p. ej. `"UPDATE 1"`).

        Raises:
            PostgreSQLBaseException: error al ejecutar la sentencia.
        """
        try:
            pool = await PostgreSQLConnection.get_pool(self._dsn)
            async with pool.acquire() as connection:
                status: str = await connection.execute(query, *args)
                return status
        except asyncpg.PostgresError as e:
            raise PostgreSQLBaseException(f"Error al escribir en PostgreSQL: {e}") from None

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[asyncpg.Connection]:
        """Abre una conexión con una transacción para operaciones que deben ser atómicas.

        Yields:
            Conexión con una transacción abierta; se confirma al salir sin error.

        Raises:
            PostgreSQLBaseException: error al ejecutar alguna sentencia dentro de la transacción.
        """
        pool = await PostgreSQLConnection.get_pool(self._dsn)
        async with pool.acquire() as connection, connection.transaction():
            try:
                yield connection
            except asyncpg.PostgresError as e:
                raise PostgreSQLBaseException(f"Error en transacción de PostgreSQL: {e}") from None
