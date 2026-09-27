# Estados del tablero

**Las skills mueven la tarjeta.** Cuando una skill completa el trabajo que
justifica un estado, lo transiciona ella misma y registra el tiempo invertido.
Así el tablero refleja el avance real sin depender de que alguien se acuerde
de arrastrar la tarjeta.

| Estado | Significado | Quién mueve aquí |
|---|---|---|
| **00.TODO** | Registrado y analizado, sin empezar | Quien registra el issue |
| **01.DESIGN** | Plan técnico generado, pendiente de aprobación | `/analisis-spec`, al generar el plan |
| **02.DEVELOPS** | Implementación en curso | `/implementacion-plan` y `/solucionar-fix`, al terminar el código |
| **03.REVISION** | PR abierto, pendiente de revisión | El desarrollador, al abrir el PR |
| **04.READYFORQA** | Mergeado, esperando validación | El Tech Lead, tras mergear |
| **DEPRECATED** | Descartado | Decisión humana |
| **DONE** | Validado y cerrado | QA, tras validar |

Las transiciones que no nacen de una skill — 03.REVISION, 04.READYFORQA y
DONE — dependen de un gesto humano: publicar el PR, mergearlo o validar en QA.
La skill que precede a una de ellas se lo recuerda al usuario al terminar.

## Cómo transicionar

Los identificadores de transición varían entre proyectos, así que no los
inventes: pide las transiciones disponibles con `mcp__jira__jira_get_transitions`,
localiza la que lleva al estado destino y aplícala con
`mcp__jira__jira_transition_issue`.

Si ninguna transición lleva al estado que buscas, no fuerces otra: informa al
usuario del estado actual y de las transiciones que sí existen, y deja que
decida.

Registra el tiempo invertido con `mcp__jira__jira_add_worklog` en la misma fase
de cierre, antes de mostrar el resumen final.

## Si el issue no está en el estado que la skill exige

Díselo al usuario y deja que decida: puede que la tarjeta esté sin actualizar,
o puede que el key sea equivocado.

> `{KEY}` está en `{estado actual}`, pero esta skill opera sobre
> `{estado esperado}`. Muévelo en Jira si el trabajo ya está en ese punto.

## Cómo leer el estado

**No compares por nombre literal.** Los tableros varían entre proyectos, y un
nombre que no coincida da un falso negativo.

Lee el campo `status` con `mcp__jira__jira_get_issue` y compáralo sin
distinguir mayúsculas ni acentos, aceptando la variante más cercana
(`04.READYFORQA` ≈ `Ready for QA` ≈ `04.QA`). Si no reconoces el estado,
muéstralo tal cual y deja que el usuario juzgue.

## Estados que detienen una skill

Antes de operar sobre un issue, comprueba su estado actual:

- **DEPRECATED** → detente. El trabajo se descartó:

  > ⛔ `{KEY}` está en DEPRECATED. Si sigue vigente, reábrelo antes de continuar.

- **DONE** → advierte antes de seguir. Trabajar sobre algo cerrado suele ser
  un error de key.
