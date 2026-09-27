class AuthenticateUserException(Exception):
    """Error no atribuible al cliente al autenticar (p. ej. JWKS inaccesible): se responde 503."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
