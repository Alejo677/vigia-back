# Revisión de PR #1 — Feature/esp 14

**Repositorio:** Alejo677/vigia-back
**Autor:** Alejo677
**Rama:** `feature/ESP-14` → `develop`
**Fecha de revisión:** 2026-09-27T20:10:00Z
**Archivos revisados:** 48 (excluidos `uv.lock` y los `*:Zone.Identifier` eliminados, y sin entrar al detalle de prosa de `.claude/`/`.github/` — instrucciones del proyecto, no código de ESP-14)

---

## Resumen ejecutivo

El PR implementa la validación de tokens de acceso de Microsoft Entra ID en el backend (ESP-14): validador JWT contra el JWKS del tenant, resolución de rol, protección por defecto de `/api/v1` y el endpoint `GET /auth/me`. La arquitectura respeta la separación por capas de la constitución (dominio sin dependencias de infraestructura, casos de uso con su propia excepción, cascada de excepciones hasta handlers HTTP globales) y la cobertura de tests es notablemente sólida, incluyendo casos de seguridad no triviales (confusión de algoritmo, `kid` desconocido, límite de refresco del JWKS). No se encontró ningún bloqueante. Hay un hallazgo de observabilidad real (el handler de errores 500 no registra la traza) y una sugerencia de eficiencia menor.

> **Actualización:** ambos hallazgos (1 importante, 1 sugerencia) se han corregido y verificado — ver el detalle marcado "✅Resuelto" en cada comentario. Recomendación revisada: **aprobar**.

---

## Comentarios de revisión

🟡 **IMPORTANTE — ✅Resuelto — El handler de errores no controlados no registra la traza**

- **Archivo:** `src/core/exceptions/handlers.py` (líneas 22–24, función `_internal_error_handler`)
- **Problema:** `logger.error("❌ Error no controlado", extra={"path": request.url.path, "error": type(exc).__name__})` registra solo la ruta y el **nombre de la clase** de la excepción, nunca su mensaje ni la traza (`exc_info`). Es exactamente el handler que se dispara ante fallos genuinamente inesperados (`Exception` genérica) — el único que atrapa lo que nadie prevé.
- **Sugerencia:** `logger.error(..., exc_info=exc)` o `logger.exception(...)` dentro del handler, para que la traza completa quede en el log aunque el cliente solo reciba el `"Error interno"` genérico.
- **Por qué importa:** Sin traza ni mensaje, un 500 en producción se reduce a "pasó una `KeyError` en `/api/v1/algo`" — no hay forma de saber en qué línea ni por qué sin reproducirlo a mano. Es justo el escenario donde más se necesita el log.
- **Resolución:** Añadido `exc_info=exc` a `logger.error(...)` en `_internal_error_handler`. La traza completa queda en el log; el cliente sigue recibiendo solo `"Error interno"`.

---

🔵 **SUGERENCIA — ✅Resuelto — `asyncio.to_thread` en cada petición aunque la clave ya esté en caché**

- **Archivo:** `src/infrastructure/auth/entra_id_access_token_validator.py` (línea 82)
- **Problema:** `await asyncio.to_thread(self._jwks_client.get_signing_key, kid)` se ejecuta para **toda** petición autenticada, incluso cuando la clave ya está en la caché en memoria de `PyJWKClient` (el caso normal: `kid` no cambia salvo rotación del tenant). Delegar a un hilo del *executor* por defecto tiene un coste fijo de creación/entrega que no aporta nada cuando la operación real es una búsqueda en un diccionario ya cacheado.
- **Sugerencia:** Si el volumen de peticiones concurrentes lo justifica, comprobar primero si la clave ya está en la caché (`get_signing_keys()` sin forzar refresco es síncrono y barato) y reservar `asyncio.to_thread` solo para el camino que sí puede golpear la red (JWKS no cacheado o `kid` desconocido).
- **Por qué importa:** No es incorrecto — solo consume hilos del *executor* compartido más de lo necesario. Con tráfico alto podría convertirse en un cuello de botella; con el volumen esperado de una herramienta interna, es una optimización opcional, no urgente.
- **Resolución:** Nuevo método `_cached_signing_key()` que consulta `PyJWKClient.jwk_set_cache.get()` (in-memory, no toca red) antes de recurrir a `asyncio.to_thread`; el salto a hilo solo ocurre si la clave no está ya cacheada. Añadido `test_validate_with_cached_kid_does_not_fetch_jwks_again`.

---

✅ **DESTACADO — Orden correcto de excepciones en `_REJECTION_BY_ERROR`**

- **Archivo:** `src/infrastructure/auth/entra_id_access_token_validator.py` (líneas 30–39)
- La tabla de mapeo coloca `PyJWKClientConnectionError` antes que su padre `PyJWKClientError`, e `InvalidSignatureError` antes que su padre `DecodeError`. Es fácil invertir este orden por descuido y acabar clasificando un fallo de red del JWKS como "firma inválida" — el comentario explica exactamente por qué el orden importa, y los tests (`test_validate_when_jwks_unreachable_raises_keys_unavailable`, `test_validate_with_hs256_token_raises_invalid_signature`) lo confirman.

---

✅ **DESTACADO — Configuración con fallo cerrado por defecto**

- **Archivos:** `src/core/configuration/settings.py` (líneas 25–29, `cors_origins()`) y `src/core/configuration/settings.py` (campos `entra_tenant_id`/`entra_api_client_id` sin valor por defecto)
- Sin `CORS_ALLOWED_ORIGINS` configurado, ningún origen puede llamar a la API (`[]`, no un comodín); sin `ENTRA_TENANT_ID`/`ENTRA_API_CLIENT_ID`, la aplicación ni siquiera arranca. Ambos son fallos cerrados razonables para una API que va a exponerse detrás de un App Service — mejor un arranque roto y evidente que un CORS abierto por omisión.

---

## Resumen de hallazgos

| Severidad | Cantidad | Resueltos |
|-----------|----------|-----------|
| 🔴 BLOQUEANTE | 0 | — |
| 🟡 IMPORTANTE | 1 | 1 |
| 🔵 SUGERENCIA | 1 | 1 |
| ✅ DESTACADO | 2 | — |

**Recomendación final:**
~~🟡 **APROBAR CON SUGERENCIAS**~~ → ✅ **APROBAR** — Los 2 hallazgos accionables se han corregido: el handler de 500 ahora registra la traza completa (`exc_info`), y el validador evita el salto a hilo cuando la clave del JWKS ya está en caché. Verificado con `ruff`, `mypy --strict` y `pytest`: **38/38 tests en verde** (37 originales + 1 nuevo).
