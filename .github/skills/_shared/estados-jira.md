# Estados del tablero

**Las skills no mueven tarjetas.** Mover un issue es el gesto con el que una
persona aprueba lo que hay debajo, así que lo hace ella. Una skill puede
consultar el estado, exigir que sea el correcto para operar y recordar que
falta moverlo — nunca transicionarlo.

| Estado | Significado | Quién mueve aquí |
|---|---|---|
| **00.TODO** | Registrado y analizado, sin empezar | Quien registra el issue |
| **01.DESIGN** | Plan técnico en diseño o pendiente de aprobación | Quien arranca el análisis |
| **02.DEVELOPS** | Implementación en curso | El desarrollador, al empezar |
| **03.REVISION** | PR abierto, pendiente de revisión | El desarrollador, al abrir el PR |
| **04.READYFORQA** | Mergeado, esperando validación | El Tech Lead, tras mergear |
| **DEPRECATED** | Descartado | Decisión humana |
| **DONE** | Validado y cerrado | QA, tras validar |

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
