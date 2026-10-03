from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities.prompt_template import PromptTemplate
from src.domain.entities.prompt_template_version import PromptTemplateVersion


class PromptTemplateVersionResponse(BaseModel):
    """Entrada del historial de versiones anteriores de una plantilla."""

    version: int
    name: str
    template: str
    alert_keywords: list[str]
    created_at: datetime | None
    created_by: str

    @classmethod
    def from_entity(cls, version: PromptTemplateVersion) -> "PromptTemplateVersionResponse":
        """Convierte una entrada de historial en su respuesta.

        Args:
            version: entrada de historial de dominio.

        Returns:
            Respuesta con los datos de la versión anterior.
        """
        return cls(
            version=version.version,
            name=version.name,
            template=version.template,
            alert_keywords=version.alert_keywords,
            created_at=version.created_at,
            created_by=version.created_by,
        )


class PromptTemplateResponse(BaseModel):
    """Plantilla de prompt tal como se expone en el listado y el detalle."""

    id: UUID
    category: str
    identifier: str
    name: str
    template: str
    alert_keywords: list[str]
    version: int
    enabled: bool
    created_at: datetime | None
    created_by: str
    updated_at: datetime | None
    updated_by: str

    @classmethod
    def from_entity(cls, template: PromptTemplate) -> "PromptTemplateResponse":
        """Convierte la entidad de dominio en su respuesta.

        Args:
            template: plantilla de dominio, ya persistida (con `id`).

        Returns:
            Respuesta con los datos de la plantilla.
        """
        if template.id is None:
            raise ValueError("La plantilla debe estar persistida para construir la respuesta")
        return cls(
            id=template.id,
            category=template.key.category,
            identifier=template.key.identifier,
            name=template.name,
            template=template.template,
            alert_keywords=template.alert_keywords,
            version=template.version,
            enabled=template.enabled,
            created_at=template.created_at,
            created_by=template.created_by,
            updated_at=template.updated_at,
            updated_by=template.updated_by,
        )


class PromptTemplateDetailResponse(PromptTemplateResponse):
    """Detalle de una plantilla, incluyendo el historial de versiones anteriores."""

    versions: list[PromptTemplateVersionResponse]

    @classmethod
    def from_entity_with_history(
        cls, template: PromptTemplate, versions: list[PromptTemplateVersion]
    ) -> "PromptTemplateDetailResponse":
        """Construye el detalle a partir de la plantilla vigente y su historial.

        Args:
            template: plantilla de dominio vigente.
            versions: versiones anteriores, más reciente primero.

        Returns:
            Respuesta de detalle con el historial incluido.
        """
        base = PromptTemplateResponse.from_entity(template)
        return cls(
            **base.model_dump(),
            versions=[PromptTemplateVersionResponse.from_entity(v) for v in versions],
        )
