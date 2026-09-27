#!/usr/bin/env python3
"""
play_youtube_genre.py

Busca un genero musical en YouTube y abre la pagina de resultados en el
navegador para que el usuario elija que reproducir.

Uso:
    python3 play_youtube_genre.py "lofi hip hop"
    python3 play_youtube_genre.py            # usa "Chillout" por defecto

Solo usa la libreria estandar de Python (urllib + webbrowser), sin
dependencias externas que instalar.
"""
import sys
import urllib.parse
import webbrowser

DEFAULT_GENRE = "Chillout"


def build_search_url(genre: str) -> str:
    query = urllib.parse.quote_plus(genre)
    return f"https://www.youtube.com/results?search_query={query}"


def main(argv) -> int:
    genre = " ".join(argv[1:]).strip() or DEFAULT_GENRE
    search_url = build_search_url(genre)

    print(f"Abriendo resultados de YouTube para: {genre!r}")
    webbrowser.open(search_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
