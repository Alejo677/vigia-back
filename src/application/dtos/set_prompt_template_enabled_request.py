from dataclasses import dataclass, replace
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SetPromptTemplateEnabledRequest:
    """Petición de activar o desactivar una plantilla de prompt (ESP-13). `id` y `updated_by` los
    completa el router a partir de la ruta y del usuario autenticado.
    """

    enabled: bool
    id: UUID | None = None
    updated_by: str = ""

    def with_id_and_user(self, template_id: UUID, email: str) -> "SetPromptTemplateEnabledRequest":
        """Devuelve una copia con el identificador de la ruta y el usuario autenticado.

        Args:
            template_id: identificador tomado del path de la URL.
            email: email del usuario autenticado.

        Returns:
            Copia de la petición con `id` y `updated_by` completados.
        """
        return replace(self, id=template_id, updated_by=email)
