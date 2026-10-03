from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.prompt_template import PromptTemplate
from src.domain.entities.prompt_template_version import PromptTemplateVersion
from src.domain.value_objects.prompt_template_key import PromptTemplateKey


class IPromptTemplateRepository(ABC):
    """Contrato de persistencia de plantillas de prompt (ESP-13)."""

    @abstractmethod
    async def save(self, template: PromptTemplate) -> PromptTemplate:
        """Crea una plantilla nueva en versión 1.

        Args:
            template: plantilla a crear, sin `id`.

        Returns:
            Plantilla creada, con `id` asignado.
        """
        ...

    @abstractmethod
    async def save_new_version(self, template: PromptTemplate) -> PromptTemplate:
        """Guarda la versión anterior en el historial y actualiza la plantilla a la nueva versión.

        Args:
            template: plantilla con los datos ya actualizados y `version` incrementada.

        Returns:
            Plantilla actualizada.
        """
        ...

    @abstractmethod
    async def update_enabled(self, template_id: UUID, enabled: bool, updated_by: str) -> PromptTemplate:
        """Activa o desactiva una plantilla.

        Args:
            template_id: identificador de la plantilla.
            enabled: nuevo estado.
            updated_by: usuario que realiza el cambio.

        Returns:
            Plantilla actualizada.
        """
        ...

    @abstractmethod
    async def delete(self, template_id: UUID) -> None:
        """Elimina físicamente una plantilla y su historial de versiones.

        Args:
            template_id: identificador de la plantilla.
        """
        ...

    @abstractmethod
    async def get_by_id(self, template_id: UUID) -> PromptTemplate | None:
        """Busca una plantilla por su identificador técnico.

        Args:
            template_id: identificador de la plantilla.

        Returns:
            La plantilla, o None si no existe.
        """
        ...

    @abstractmethod
    async def get_active_by_key(self, key: PromptTemplateKey) -> PromptTemplate | None:
        """Busca la plantilla activa de una categoría e identificador exactos.

        Args:
            key: categoría e identificador exactos.

        Returns:
            La plantilla activa, o None si no existe o está desactivada.
        """
        ...

    @abstractmethod
    async def exists_with_key(self, key: PromptTemplateKey) -> bool:
        """Indica si ya existe una plantilla con esa categoría e identificador (Regla 2).

        Args:
            key: categoría e identificador a comprobar.

        Returns:
            True si ya existe una plantilla con esa clave.
        """
        ...

    @abstractmethod
    async def count_active_with_identifier_in_category(self, category: str, identifier: str) -> int:
        """Cuenta las plantillas activas con ese identificador dentro de la categoría (Regla 3).

        Args:
            category: categoría a comprobar.
            identifier: identificador a comprobar (normalmente `generico`).

        Returns:
            Número de plantillas activas con esa categoría e identificador.
        """
        ...

    @abstractmethod
    async def list_versions(self, template_id: UUID) -> list[PromptTemplateVersion]:
        """Lista el historial de versiones anteriores de una plantilla, más reciente primero.

        Args:
            template_id: identificador de la plantilla.

        Returns:
            Versiones anteriores conservadas en el historial.
        """
        ...

    @abstractmethod
    async def list(
        self,
        page: int,
        page_size: int,
        search: str | None,
        category: str | None,
        sort_by: str,
        sort_dir: str,
    ) -> tuple[list[PromptTemplate], int]:
        """Lista plantillas paginadas, con el `generico` de cada categoría al inicio de su grupo.

        Args:
            page: número de página (1-indexado).
            page_size: tamaño de página.
            search: búsqueda libre por categoría, identificador o nombre.
            category: filtro exacto por categoría.
            sort_by: columna de ordenación.
            sort_dir: dirección de ordenación (`asc` / `desc`).

        Returns:
            Página de plantillas y el total de resultados sin paginar.
        """
        ...
