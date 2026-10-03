from dataclasses import dataclass, field, replace


@dataclass(frozen=True, slots=True)
class CreatePromptTemplateRequest:
    """Petición de alta de una plantilla de prompt (ESP-13). `created_by` lo añade el router
    a partir del usuario autenticado, nunca lo envía el cliente.
    """

    category: str
    identifier: str
    name: str
    template: str
    alert_keywords: list[str] = field(default_factory=list)
    enabled: bool = True
    created_by: str = ""

    def with_user(self, email: str) -> "CreatePromptTemplateRequest":
        """Devuelve una copia con el usuario autenticado como autor del alta.

        Args:
            email: email del usuario autenticado.

        Returns:
            Copia de la petición con `created_by` completado.
        """
        return replace(self, created_by=email)
