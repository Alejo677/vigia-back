from dataclasses import dataclass, field, replace
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UpdatePromptTemplateRequest:
    """Petición de modificación de una plantilla de prompt: crea una nueva versión (ESP-13, Regla 5).

    El identificador no se incluye: es inmutable tras el alta (ESP-13, Regla 2). `updated_by` lo
    añade el router a partir del usuario autenticado, nunca lo envía el cliente.
    """

    name: str
    template: str
    alert_keywords: list[str] = field(default_factory=list)
    id: UUID | None = None
    updated_by: str = ""

    def with_id_and_user(self, template_id: UUID, email: str) -> "UpdatePromptTemplateRequest":
        """Devuelve una copia con el identificador de la ruta y el usuario autenticado.

        Args:
            template_id: identificador tomado del path de la URL.
            email: email del usuario autenticado.

        Returns:
            Copia de la petición con `id` y `updated_by` completados.
        """
        return replace(self, id=template_id, updated_by=email)
