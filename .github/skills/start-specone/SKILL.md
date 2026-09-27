---
name: start-specone
description: Abre YouTube en el navegador externo del sistema y reproduce automáticamente el primer resultado para un género musical (por defecto Chillout). Úsalo cuando el usuario pida poner o reproducir música/un género en YouTube.
parametros:
- género: El género de música que se desea reproducir en YouTube. Por defecto es **Chillout**.
argument-hint: "Tchaikovsky Concert Hall"
---

## Reproducir música por género en YouTube

Cuando el usuario pida "pon música de <género> en YouTube", "reproduce algo de <género>"
o similar, y no especifique un género, usa por defecto **Chillout**.

Para cumplir la petición:

1. Asegúrate de que `.github/skills/start-specone/play_youtube_genre.py` existe en el repo.

2. Ejecuta en la terminal: `python3 .github/skills/start-specone/play_youtube_genre.py "<género>"`.

3. El script se encarga de buscar en YouTube y abrir el **navegador externo del sistema**
   (Chrome, Edge, Firefox…) ya reproduciendo el primer resultado.

4. Confirma al usuario el género buscado o indicar si no se encontró el script.

## Navegador: siempre externo

La reproducción debe ocurrir **siempre en el navegador externo del sistema operativo**,
nunca dentro del IDE.

- **Obligatorio:** abrir la URL mediante el script, que usa el navegador por defecto del SO.
- **Prohibido:** usar el Simple Browser de VS Code, la vista previa/navegador integrado de
  VS Code o de cualquier otro IDE, ni herramientas de navegador embebido o automatizado
  del agente (por ejemplo `open_browser_page`, `navigate_page` o similares).
- **Prohibido** incrustar el reproductor en un webview, panel o pestaña del editor.
- Si el script falla, no abras la URL en un navegador integrado como alternativa: informa
  al usuario y, como mucho, indícale el enlace para que lo abra él en su navegador.