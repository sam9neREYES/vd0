"""Banner de vd0: el nombre dibujado con números, al estilo de las
herramientas clásicas de Linux, seguido de una leyenda del programa."""

from __future__ import annotations

import os
import sys

from . import __version__

# Cada letra es una matriz de 7 filas. '#' = píxel encendido.
GLYPHS = {
    "v": [
        "##...##",
        "##...##",
        "##...##",
        ".##.##.",
        ".##.##.",
        "..###..",
        "...#...",
    ],
    "d": [
        ".....##",
        ".....##",
        ".######",
        "##...##",
        "##...##",
        "##...##",
        ".######",
    ],
    "0": [
        ".#####.",
        "##...##",
        "##..###",
        "##.#.##",
        "###..##",
        "##...##",
        ".#####.",
    ],
}

NAME = "vd0"
DIGITS = "10"  # los píxeles se rellenan con unos y ceros alternados
GAP = "   "
# Degradado cian -> azul -> violeta (colores ANSI de 256)
ROW_COLORS = [51, 45, 39, 33, 27, 63, 99]


def enable_ansi() -> None:
    """Activa los colores ANSI en consolas de Windows y ajusta UTF-8."""
    if os.name == "nt":
        os.system("")  # activa el procesamiento de secuencias VT en Windows 10+
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


def use_color() -> bool:
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def render_name(color: bool = True) -> str:
    """Devuelve el nombre 'vd0' dibujado con dígitos."""
    lines = []
    for r in range(7):
        parts = []
        for ci, ch in enumerate(NAME):
            row = GLYPHS[ch][r]
            parts.append(
                "".join(
                    DIGITS[(r + c + ci) % len(DIGITS)] if px == "#" else " "
                    for c, px in enumerate(row)
                )
            )
        line = GAP.join(parts)
        if color:
            line = f"\033[1;38;5;{ROW_COLORS[r]}m{line}\033[0m"
        lines.append("  " + line)
    return "\n".join(lines)


def legend(color: bool = True) -> str:
    b = "\033[1m" if color else ""
    d = "\033[2m" if color else ""
    c = "\033[36m" if color else ""
    r = "\033[0m" if color else ""
    return (
        f"\n  {b}vd0 v{__version__}{r} {d}- Descargador de videos desde la terminal{r}\n"
        f"  {d}{'-' * 62}{r}\n"
        "  Descarga videos (o solo el audio) pegando el enlace de:\n"
        "    YouTube, Facebook, Instagram, TikTok, X/Twitter, Vimeo,\n"
        "    Reddit, Twitch, Dailymotion y mas de 1000 sitios compatibles.\n"
        "\n"
        f"  {b}Uso:{r}\n"
        f'    {c}vd0 "url"{r}                      descarga el video en la mejor calidad\n'
        f'    {c}vd0 -a "url"{r}                   descarga solo el audio (MP3)\n'
        f'    {c}vd0 -q 720 "url"{r}               limita la calidad a 720p\n'
        f'    {c}vd0 -o ~/Videos "url"{r}          elige la carpeta de destino\n'
        f"    {c}vd0 -h{r}                         muestra todas las opciones\n"
        "\n"
        f"  {d}Funciona con usuario normal y como administrador (sudo / PowerShell admin).{r}\n"
        f"  {d}Usalo solo con contenido propio, libre o con permiso de su autor.{r}\n"
    )


def print_banner(color: bool | None = None) -> None:
    color = use_color() if color is None else color
    print()
    print(render_name(color))
    print(legend(color))


def compact_header(color: bool | None = None) -> str:
    color = use_color() if color is None else color
    if color:
        return f"\033[1;38;5;45mvd0\033[0m \033[2mv{__version__}\033[0m"
    return f"vd0 v{__version__}"
