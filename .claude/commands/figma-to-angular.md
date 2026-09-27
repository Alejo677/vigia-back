---
name: figma-to-angular
description: |
  Convierte un diseño de Figma en Angular nodo a nodo vía MCP, enumerando todas
  las variantes de cada componente para que ninguna se pierda. Termina con una
  comprobación mecánica de completitud que falla si queda algo sin implementar.
  Requiere el MCP de Figma conectado y Python 3.10+.
  Úsala cuando se pegue una URL de Figma, se mencione un diseño o mockup, o se
  pida implementar, replicar o auditar una pantalla o design system en Angular.
  Parámetros: "<URL de Figma o node-id>" [KEY_JIRA]
  Ejemplo: /figma-to-angular https://figma.com/design/abc/Home?node-id=1-2 IAFIT-55
argument-hint: "<URL de Figma o node-id> [KEY_JIRA]"
---

Actúa como implementador de diseños. Convierte el nodo de Figma indicado en
código Angular que respete las convenciones del repositorio.

`$ARGUMENTS`: primer token = URL de Figma o `node-id`. Segundo token opcional =
`KEY_JIRA`; si se indica, el trabajo se registra contra ese issue y el manifiesto
se guarda como `docs/figma/{KEY}.md` en vez de `figma-manifest.md`.

El fallo que esta skill existe para evitar es la **omisión silenciosa**:
implementar la variante por defecto, escribir `<!-- el resto sigue el mismo
patrón -->` y reportar éxito. El diseño parece correcto al 90% y el 10% que
falta aparece en QA semanas después.

La contramedida es estructural, no motivacional: inventario antes de
implementar, lotes para que el contexto no desborde a mitad de componente, y
una comprobación mecánica que falla de forma ruidosa.

---

## Innegociables

1. **Nunca abrevies el código generado.** Ni `// ...`, ni "igual que arriba", ni
   "por brevedad". Si un componente tiene 24 combinaciones de variantes, las 24
   son alcanzables en el código.
2. **Nunca decidas que una variante sobra.** Si una combinación parece
   redundante, impleméntala y señálala en el informe — no la descartes en
   silencio.
3. **Nunca implementes desde una captura si hay datos estructurados.** Las
   capturas son sólo para verificar.
4. **Detente e informa en vez de adivinar.** Token que falta, componente sin
   mapear, comportamiento indefinido → lista de preguntas abiertas, nunca un
   valor inventado.
5. **Nunca declares completado sin ejecutar la comprobación** (Paso 6).

---

## Referencias

`.github/skills/figma-to-angular/references/angular-mapping.md` tiene las
reglas de mapeo. Carga las secciones cuando el paso las necesite, no todas de
golpe:

| Sección | Se lee en |
|---|---|
| Structural mapping, Variants | Paso 1, antes de enumerar variantes |
| Tokens, Typography | Paso 2 |
| Assets | Paso 3, antes de decidir cómo se tratan los iconos |
| Auto Layout → CSS, Responsive, Interaction states, Accessibility | Paso 4, por lote |

---

## Paso 0 — Fijar el objetivo

### Comprobación previa: el MCP de Figma responde

Hazlo primero. Todos los pasos a partir del 1 llaman a una herramienta MCP, así
que un servidor ausente mata la ejecución a mitad de inventario con un error
confuso en vez de uno útil.

Verifica que tienes disponibles `get_metadata`, `get_design_context`,
`get_variable_defs`, `get_code_connect_map` y `get_screenshot`.

**Si no están, detente e informa** — no continúes, y no recurras a capturas ni a
adivinar desde la URL. Indica al usuario:

> El MCP de Figma no está conectado, así que no puedo leer el diseño.
>
> En Claude Code, añade el servidor MCP de Figma (`claude mcp add` o vía
> `/mcp`) y asegúrate de que está autorizado y disponible en la sesión.
>
> `specone doctor` comprueba esto mismo.

Una skill que reporta un requisito ausente es útil. Una que improvisa alrededor
produce código plausible que no corresponde a ningún diseño, que es peor que no
producir nada.

### Después, confirma desde el repositorio, no desde el usuario

- **Versión de Angular** (`package.json`). 20+ tiene signal inputs y control de
  flujo integrado; 21+ es zoneless por defecto; 22+ añade componentes sin
  selector y Signal Forms estables. Ajústate al repo, no lo actualices.
- **Sistema de estilos**: SCSS, Tailwind, CSS Modules o una librería existente.
- **Tokens de diseño** (`_tokens.scss`, fichero de tema, custom properties).
  Extiéndelos en vez de crear un sistema paralelo.
- **Convenciones de componente**: lee 2–3 componentes existentes y replica su
  estructura, nombres, organización de ficheros y estrategia de detección de
  cambios.
- **Sistema de iconos**: `lucide-angular`, `@ng-icons`, un `IconComponent`
  propio, un sprite SVG, o ninguno.
- **Directorio de assets**: dónde viven ya los estáticos (`src/assets/`,
  `public/`, otro).

Si el proyecto tiene `CONSTITUCION.md` o ficheros de instructions, sus reglas
mandan sobre cualquier convención que deduzcas del código.

### Si el repositorio está vacío o casi

Un `ng new` recién creado no tiene componentes que imitar ni tokens que
extender, así que las convenciones tienen que salir de algún sitio. Declara los
valores por defecto que adoptas, en el informe final y en el manifiesto, para
que sean visibles y puedan corregirse en vez de absorberse en silencio:

- Componentes standalone, `OnPush`, signal inputs (`input()`), control de flujo
  integrado (`@if`, `@for`).
- Un directorio por componente: `.ts`, `.html`, `.scss`.
- Tokens como custom properties en `:root` de una hoja global.
- Iconos como un `.svg` por fichero en `src/assets/icons/`, con `currentColor`.

Dilo explícitamente: *"El repositorio no tiene componentes previos, así que
establezco estas convenciones — dime si prefieres otras."* En un repo vacío, lo
primero que se genera se convierte en la convención de todo lo que venga
después, y eso vale una frase de confirmación.

---

## Paso 1 — Inventario (nunca lo saltes)

El inventario es lo que hace detectable la omisión más adelante.

Llama a `get_metadata` sobre el nodo raíz — XML escueto con identificadores,
nombres, tipos, posiciones y tamaños. Barato de ejecutar sobre una página
entera, a diferencia de `get_design_context`.

Escribe el manifiesto usando
`.github/skills/figma-to-angular/references/manifest-template.md`:

- Sin `KEY_JIRA` → `figma-manifest.md` en la raíz.
- Con `KEY_JIRA` → `docs/figma/{KEY}.md`.

Cada nodo que se convierta en marcado lleva una casilla sin marcar y su
identificador de Figma.

Después, para cada `COMPONENT_SET`, llama a `get_design_context` sobre el
conjunto y enumera el **producto cartesiano completo de sus propiedades de
variante**. `state: default|hover|pressed|disabled` × `size: sm|md|lg` ×
`icon: none|left|right` son 36 combinaciones y 36 líneas de manifiesto. Un
agente que no las escribió es un agente que las va a olvidar.

Reporta los totales antes de continuar: nodos, componentes, combinaciones de
variante. Por encima de ~150 combinaciones, dilo y propón repartir el trabajo en
varias sesiones en vez de degradar en silencio.

---

## Paso 2 — Tokens primero

Llama a `get_variable_defs` sobre la raíz, una vez.

Genera la capa de tokens antes que cualquier componente — todo lo demás depende
de ella. Mapea los nombres de variable de Figma a custom properties conservando
la semántica: `color/surface/raised` → `--color-surface-raised`. Nunca emitas un
hex o un px crudo si existe un token equivalente; los valores incrustados rompen
el theming de forma invisible.

Anota en preguntas abiertas cualquier valor sin variable correspondiente.

---

## Paso 3 — Reutilizar antes que generar

Llama a `get_code_connect_map` — devuelve nombre real, ruta de importación e
interfaz de props de cada nodo mapeado.

Para cada nodo mapeado: importa y usa el componente existente. Generar un botón
duplicado cuando ya existe `<app-button>` fragmenta el design system, que es
peor que una reutilización imperfecta.

Para nodos sin mapear que claramente corresponden a un componente existente,
pregunta antes de generar un duplicado.

Decide ahora cómo se tratan **iconos e imágenes**, antes de escribir ningún
componente — lee la sección Assets de
`.github/skills/figma-to-angular/references/angular-mapping.md`. Si el repo
tiene librería de iconos, mapea sobre ella. Si no, cada icono es su propio
`.svg` en vez de marcado pegado en las plantillas. Decidir esto por componente
es como un código acaba con el mismo icono incrustado seis veces.

Para imágenes, elige el formato por lo que el asset **es** — vectorial a `.svg`,
fotografía a `.webp` — no por lo que devuelva Figma. Renombra a `kebab-case`
según la capa; nunca conserves el nombre exportado por Figma. Al reportar los
assets exportados, agrúpalos por el componente que los usa, no por tipo de
fichero: una lista ordenada por extensión no se puede contrastar con el
manifiesto.

---

## Paso 4 — Implementar por lotes

Como máximo **5 componentes hoja o 1 conjunto de componentes** por pasada. El
límite no es arbitrario: agotar el contexto a mitad de componente es lo que
produce la salida abreviada que prohíbe el innegociable 1. Los lotes pequeños
mantienen a la vista el marcado de todas las variantes.

Por lote:

1. Llama a `get_design_context` sobre el nodo concreto. Nombra Angular y el
   sistema de estilos del repo explícitamente — el servidor asume React +
   Tailwind si no se le dice otra cosa.
2. Escribe el componente: plantilla, estilos, inputs tipados para cada propiedad
   de variante.
3. Marca en el manifiesto exactamente los nodos implementados.
4. No empieces el siguiente lote hasta que el actual compile.

Nunca retengas más de un lote de contexto de diseño. Pide, implementa, marca,
descarta.

---

## Paso 5 — Verificar visualmente

Llama a `get_screenshot` sobre el nodo de Figma y compara con el componente
renderizado, en este orden — ordenado por frecuencia de error: espaciado y
padding, grosor de fuente y letter-spacing, radio de borde, extensión y opacidad
de sombra, tamaño y alineación óptica de iconos, y cada estado no por defecto.

Los estados se esconden. Una variante `hover` desviada 4px no se detecta jamás
mirando la de por defecto.

---

## Paso 6 — Demostrar completitud

Mecánico a propósito — la autoevaluación es exactamente lo que falla aquí:

```bash
python .github/skills/figma-to-angular/scripts/check_completeness.py \
  --manifest figma-manifest.md --src src/app
```

Con `KEY_JIRA`, el manifiesto es `docs/figma/{KEY}.md`.

Falla ante casillas sin marcar, frases de relleno en el código generado, y
propiedades de variante declaradas en el manifiesto pero ausentes de los inputs
del componente.

Corrige y repite hasta que pase. No reportes completado mientras falle, y no
edites el manifiesto para que pase.

---

## Informe final

- **Cobertura**: nodos implementados / totales, combinaciones de variante
  implementadas / totales.
- **Reutilizado vs generado**: qué componentes vinieron de Code Connect.
- **Diferencias con el diseño**: toda divergencia consciente, y por qué. "Sombra
  de la tarjeta aproximada, Figma usa doble sombra que CSS no expresa en una
  propiedad" es útil; "diferencias menores de estilo" no lo es.
- **Preguntas abiertas**: tokens ausentes, estados ambiguos, comportamiento
  responsive sin definir.

Una lista de diferencias corta y honesta vale más que una afirmación de
perfección. Esconder las diferencias sólo mueve el descubrimiento a producción.

---

## Dónde encaja en el ciclo

Esta skill produce código, igual que `/implementacion-plan`. La diferencia es el
origen: el plan viene de un análisis escrito, aquí viene de un diseño.

- Con `KEY_JIRA`, deja el issue donde estaba: **no** transiciona el tablero.
  Cuando el código esté listo, `/implementacion-plan` o `/ajustar-implementacion`
  se encargan del flujo de rama y PR.
- Sin `KEY_JIRA`, es una implementación suelta: útil para prototipos y para
  construir un design system antes de que haya issues.
