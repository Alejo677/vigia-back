---
name: start-specone
description: Abre YouTube en el navegador externo del sistema y reproduce automáticamente el primer resultado para un género musical (por defecto Chillout). Úsalo cuando el usuario pida poner o reproducir música/un género en YouTube.
parametros:
- género: El género de música que se desea reproducir en YouTube. Por defecto es **Chillout**.
argument-hint: "Tchaikovsky Concert Hall"
---

# youtube-genre-play

Este skill busca un género musical en YouTube y reproduce automáticamente
el primer resultado (no solo abre la página de búsqueda: entra al vídeo y
lo pone en autoplay) en el **navegador externo del sistema**.

## Cuándo usarlo

El usuario pide cosas como "pon música chillout en YouTube", "reproduce
techno", "abre YouTube y pon algo de jazz", "pon música" (sin más detalle).

## Parámetro

- Género musical, en el idioma que use el usuario (p. ej. "lofi hip hop",
  "techno", "jazz").
- Si el usuario no da ningún género, usa por defecto: **Chillout**.

## Pasos

1. Comprueba que `.claude/scripts/play_youtube_genre.py` existe en el directorio de
   trabajo actual.

2. Ejecuta el script con el género como argumento:

   ```bash
   python3 .claude/scripts/play_youtube_genre.py "<genero>"
   ```

   Esto abre el **navegador externo por defecto del sistema** directamente en el primer
   vídeo encontrado, con autoplay activado.

3. Confirma al usuario el género buscado o indica si no se encontró el script.

## Navegador: siempre externo

La reproducción debe ocurrir **siempre en el navegador externo del sistema operativo**,
nunca dentro del IDE.

- **Obligatorio:** abrir la URL mediante el script, que usa el navegador por defecto del SO.
- **Prohibido:** usar el Simple Browser de VS Code, el navegador o vista previa integrada
  de VS Code o de cualquier otro IDE, ni herramientas de navegador embebido/automatizado
  del agente (Playwright, `open_browser_page`, `navigate_page` o similares).
- **Prohibido** incrustar el reproductor en un webview, panel o pestaña del editor.
- Si el script falla, no abras la URL en un navegador integrado como alternativa: informa
  al usuario y, como mucho, indícale el enlace para que lo abra él en su navegador.
