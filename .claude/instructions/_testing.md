# Experto: Testing

## Filosofía

> 3 pruebas de cosas críticas > 80% de cobertura de cosas superfluas.
> Se prefieren pruebas integrales sobre unitarias.

- Los mocks son aceptables **solo** cuando hay dependencia de una historia futura o de un servicio externo no disponible localmente. Dejar `# TODO: reemplazar mock cuando se implemente <ticket>` explícito.
- Los tests de integración deben tocar la base de datos real. No simular el pool de PostgreSQL.
- Los clientes externos (GitHub, feeds, extractor de páginas, Azure OpenAI, Slack, SMTP) pueden mockearse en tests unitarios de use cases. En tests de integración se prefieren servicios reales en un entorno de pruebas o respuestas grabadas (fixtures de feeds RSS/Atom, SBOM SPDX y respuestas del LLM) cuando el servicio no es controlable.
- Los Timer Triggers y el CLI no se prueban por sí mismos: se prueban los casos de uso que invocan.

---

## Stack

```bash
pytest                               # todos los tests
pytest tests/test_foo.py::test_bar   # un test concreto
pytest -m integration                # solo integración
pytest -m unit                       # solo unitarios
```

Decoradores async: `@pytest.mark.asyncio`. Mocks: `unittest.mock.AsyncMock`.

---

## Nomenclatura

- Archivos: `test_<nombre_modulo>.py`
- Funciones: `test_<funcion>_<escenario>_<resultado_esperado>`

```python
async def test_sync_apps_with_duplicated_key_applies_no_changes():
    ...

async def test_ingest_news_with_already_ingested_entries_creates_only_new_news():
    ...

async def test_classify_news_when_llm_returns_unknown_component_discards_it_and_keeps_rest():
    ...

async def test_correlate_when_used_version_outside_affected_range_creates_no_alert():
    ...
```

---

## Patrón Arrange-Act-Assert

```python
@pytest.mark.asyncio
async def test_classify_news_with_pypi_adapter_data_and_no_alert_words_skips_llm():
    # Arrange
    news = make_news(source_code="pypi-langchain", suggested_component="pkg:pypi/langchain", version="1.4.2", title="1.4.2")
    catalog = AsyncMock(spec=ICatalogRepository)
    catalog.resolve.return_value = make_component("pkg:pypi/langchain")
    classifier = AsyncMock(spec=INewsClassifier)
    use_case = ClassifyNewsUseCase(catalog=catalog, classifier=classifier, ...)

    # Act
    result = await use_case.execute(ClassifyNewsRequest(news_ids=[news.id]))

    # Assert
    classifier.classify.assert_not_called()
    classification = result.classifications[0]
    assert classification.event_type == EventType.NEW_VERSION
    assert classification.severity == Severity.INFORMATIVE
    assert classification.model == "regla-adaptador"
```

---

## Tests de integración

- Carpeta: `tests/integration/`
- Usan conexión real a PostgreSQL (variables en `.env`).
- Para GitHub, feeds y Azure OpenAI se usan endpoints reales en un entorno de pruebas o fixtures grabadas, salvo que el ticket indique lo contrario. Nunca se envían mensajes reales a Slack ni emails reales desde los tests.
- Los endpoints del backend se prueban con el cliente de pruebas de FastAPI, incluyendo token válido, token expirado y rol insuficiente.
- Los tokens de Entra ID de los tests se firman con una clave RSA de pruebas y el validador se configura con su JWKS local (emisor y audiencia de pruebas). Nunca se obtienen tokens del tenant real ni se desactiva la validación de firma en los tests.
- No limpian datos — el estado persistente es intencional para facilitar debugging.
- Ejecutar con `pytest -m integration` (requiere BD disponible).

---

## Tests unitarios

- Carpeta: `tests/unit/`
- Aislar dependencias externas (BD, clientes externos) con `AsyncMock` o `MagicMock`.
- Usar solo para lógica de dominio pura: normalización de alias, validación de slugs y patrones de URL, filtros regex, adaptadores de ingesta, detección de prereleases, comparación de versiones, matriz de prioridad, resolución de plantillas, etc.

---

## Qué tiene prioridad de testing en este proyecto

| Área | Tipo | Por qué |
|---|---|---|
| Autenticación con Entra ID: 401 sin token, con token expirado, con firma, emisor, audiencia o *scope* incorrectos; 403 con token sin `roles`; `require_role` devuelve 403 con rol insuficiente; con ambos roles prevalece `admin` | Integración | Seguridad crítica (constitución §2.8, ESP-14) |
| Verificación de firma de Slack en la interactividad | Integración | Endpoint expuesto sin JWT |
| `scan-ai` nunca guarda valores de secretos (solo nombre de variable) | Unitario | Principio inmutable §2.3 |
| Componentes del LLM fuera del catálogo se descartan | Unitario | Principio inmutable §2.1 |
| Idempotencia de `sync-apps`, `sync-catalog`, `ingest-news` y `correlate` (segunda ejecución sin cambios) | Integración | Principio inmutable §2.5 |
| Archivos YAML inválidos o con duplicados no aplican ningún cambio | Integración | Todo-o-nada (ESP-01, ESP-03, ESP-04) |
| Deduplicación de noticias por URL canónica / `guid` y primera ingesta limitada a 30 días | Integración | Flujo crítico ESP-07 |
| Adaptadores de PyPI y GitHub, filtros de inclusión/exclusión y prereleases | Unitario | Lógica de dominio verificable (ESP-07) |
| Clasificación automática sin LLM (`regla-adaptador`) y escalado por palabras de alerta | Unitario | Coste y precisión (ESP-08, Reglas 9–11) |
| Resolución de plantilla específica → `generico` → error de configuración | Unitario | Flujo crítico ESP-13 |
| Última plantilla `generico` activa no se puede eliminar ni desactivar | Integración | Regla 3 de ESP-13 |
| Correlación: rango de versiones, "versión sin verificar", matriz de prioridad y subida por fecha < 30 días | Unitario | Núcleo del producto (ESP-09) |
| Una alerta por par noticia–aplicación | Integración | Índice único (ESP-09, Regla 2) |
| Digest: email filtrado por responsable y alertas no marcadas "notificada" si falla el envío | Unitario | ESP-10 |
| Resolución de usos solo con la última instantánea correcta | Integración | Usos vigentes (ESP-05, Regla 4) |
| Fuente con noticias asociadas no se elimina (409) | Integración | ESP-06, Regla 8 |

---

## Marcadores pytest

Configurados en `pyproject.toml`:

```ini
markers =
    integration: tests que requieren BD o servicios externos
    unit: tests de lógica pura sin dependencias externas
    slow: tests lentos (>5s)
```
