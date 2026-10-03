class ResolvePromptTemplateException(Exception):
    """Ninguna plantilla activa (específica ni `generico`) para la categoría pedida: error de
    configuración (ESP-13, Caso 3); se responde 500 porque no debería ocurrir si se respeta la Regla 3.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
