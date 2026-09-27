---
name: ajustar-plan
description: |
  Modifica un documento de plan técnico ya existente en docs/plan/ cuando hay que
  cambiar el diseño antes de implementar: reubicar lógica entre capas, corregir
  rutas de ficheros o ampliar el plan de pruebas.
  Opera sobre el CÓMO técnico, después de la spec y antes del código.
  No usar para especificaciones funcionales (usa /ajustar-spec) ni para código ya
  escrito (usa /ajustar-implementacion).
  Parámetros: "<ruta_del_plan.md>" "<ajuste técnico>"
  Ejemplo: /ajustar-plan "docs/plan/IAFIT-42.md" "Mover el filtrado de fechas al use case en vez del router"
argument-hint: "<ruta docs/plan/*.md>" "<ajuste técnico>"
---

Actúa como Arquitecto de Software Full-Stack Senior. Evalúa el impacto
arquitectónico del ajuste y actualiza el plano técnico si procede.

**No implementes código fuente.** Solo modificas el documento de diseño.

`$ARGUMENTS`: primer token entrecomillado = ruta del plan; segundo = ajuste técnico.

---

## Paso 0 — Contexto

Lee el fichero de plan indicado. Si no existe, detente.

Lee los ficheros de instructions activos del workspace (stack, capas, testing
y convenciones de código) y `CONSTITUCION.md`. Si las instructions no
existen, deriva todo de la constitución.

---

## Paso 1 — Impacto arquitectónico

Aplica las reglas arquitectónicas de `CONSTITUCION.md`: dirección de
dependencias, lógica en la capa correcta, datos sensibles, aislamiento de
features y alcance.

Es válido si corrige un error de capas, ajusta la inyección de dependencias
para respetar los `Protocol` del dominio, reorganiza ficheros hacia la
estructura correcta o robustece el plan de pruebas.

Si no es válido: **no toques el fichero**, salta al Paso 3 y reporta el rechazo.

---

## Paso 2 — Aplicar

Reescribe **quirúrgicamente** sólo los bloques afectados:

| Sección | Cuándo se toca |
|---|---|
| **3. Impacto** | El ajuste añade, quita o reubica dependencias, variables de entorno o migraciones de BD |
| **4. Backend** | Cambian rutas, acciones (Crear/Modificar) o la capa afectada |
| **5. Frontend** | Cambian rutas dentro de `features/`, `shared/` o `core/` |
| **6. Pruebas** | El ajuste altera una firma o el flujo de control. Nomenclatura `test_<funcion>_<escenario>_<resultado>` |

`Estado: pendiente de aprobacion` **no se modifica**. Sobrescribe el fichero en
su ruta.

---

## Paso 3 — Reportar consumo de tokens

Invoca `/token-spend "General" "ajustar-plan"`.

**Si se aplicó:**

```text
✅ Plan técnico ajustado

📌 Issue: <KEY_JIRA>
📂 Fichero: docs/plan/{ID}.md
📋 Estado: pendiente de aprobacion
⚠️ Cambios: [qué componentes, capas o pruebas se modificaron y cómo encajan]
```

Muestra debajo las filas de las tablas que cambiaron.

**Si se rechazó:** mismo formato con `❌ Ajuste rechazado`, indicando la regla
violada, la referencia normativa y una alternativa compatible.
