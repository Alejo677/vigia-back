class PostgreSQLBaseException(Exception):
    """Error de infraestructura al ejecutar una consulta contra PostgreSQL."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
