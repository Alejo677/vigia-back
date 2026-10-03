class TestPromptTemplateException(Exception):
    """Error no atribuible al cliente al renderizar una plantilla de prueba: se responde 502."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
