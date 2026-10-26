"""Interfaz de línea de comandos de vd0."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, List, Optional

from . import __version__
from .banner import compact_header, enable_ansi, print_banner, use_color

QUALITIES = ("best", "2160", "1440", "1080", "720", "480", "360")


# --------------------------------------------------------------------------
# Utilidades de sistema (usuario normal vs administrador)
# --------------------------------------------------------------------------
def _sudo_user_info():
    """Si corremos con sudo en Linux/macOS devuelve la info del usuario real."""
    if os.name != "posix" or os.geteuid() != 0:
        return None
    name = os.environ.get("SUDO_USER")
    if not name or name == "root":
        return None
    try:
        import pwd

        return pwd.getpwnam(name)
    except (ImportError, KeyError):
        return None


def real_home() -> Path:
    """Carpeta personal del usuario real, incluso si se ejecuta con sudo."""
    info = _sudo_user_info()
    if info is not None:
        return Path(info.pw_dir)
    return Path.home()


def default_output_dir() -> Path:
    return real_home() / "Downloads" / "vd0"


def fix_ownership(outdir: Path) -> None:
    """Con sudo, devuelve los archivos descargados al usuario real."""
    info = _sudo_user_info()
    if info is None:
        return
    home = real_home()
    targets = [outdir]
    targets.extend(outdir.rglob("*"))
    parent = outdir.parent
    while parent != home and home in parent.parents:
        targets.append(parent)
        parent = parent.parent
    for path in targets:
        try:
            os.chown(path, info.pw_uid, info.pw_gid)
        except OSError:
            pass


def find_ffmpeg() -> Optional[str]:
    """ffmpeg del sistema o, si no existe, el binario incluido en imageio-ffmpeg."""
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


# --------------------------------------------------------------------------
# Presentación
# --------------------------------------------------------------------------
def _fmt_bytes(n: Optional[float]) -> str:
    if not n:
        return "-- B"
    value = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def _progress_hook(d: dict) -> None:
    status = d.get("status")
    cols = shutil.get_terminal_size((80, 20)).columns
    if status == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        done = d.get("downloaded_bytes") or 0
        pct = (done / total * 100) if total else 0.0
        width = 24
        filled = int(width * pct / 100)
        bar = "#" * filled + "-" * (width - filled)
        speed = d.get("speed")
        eta = d.get("eta")
        eta_txt = f"{int(eta)}s" if eta is not None else "--"
        line = f"  [{bar}] {pct:5.1f}%  {_fmt_bytes(speed)}/s  ETA {eta_txt}"
        sys.stdout.write("\r" + line.ljust(cols - 1)[: cols - 1])
        sys.stdout.flush()
    elif status == "finished":
        sys.stdout.write("\r" + " " * (cols - 1) + "\r")
        print("  Descarga completa, procesando archivo...")


def _collect_paths(info: Any) -> List[str]:
    paths: List[str] = []
    if not isinstance(info, dict):
        return paths
    if info.get("entries"):
        for entry in info["entries"]:
            paths.extend(_collect_paths(entry))
        return paths
    for item in info.get("requested_downloads") or []:
        fp = item.get("filepath")
        if fp:
            paths.append(fp)
    return paths


# --------------------------------------------------------------------------
# Descarga
# --------------------------------------------------------------------------
def build_options(args: argparse.Namespace, outdir: Path, ffmpeg: Optional[str]) -> dict:
    opts: dict = {
        "outtmpl": str(outdir / "%(title).150B [%(id)s].%(ext)s"),
        "noplaylist": not args.playlist,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "progress_hooks": [_progress_hook],
        "windowsfilenames": True,
        "retries": 10,
        "fragment_retries": 10,
        "concurrent_fragment_downloads": 4,
    }
    if ffmpeg:
        opts["ffmpeg_location"] = ffmpeg

    if args.audio:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
    else:
        if args.quality == "best":
            opts["format"] = "bv*+ba/b"
        else:
            h = args.quality
            opts["format"] = f"bv*[height<={h}]+ba/b[height<={h}]/bv*+ba/b"
        # Prefiere mp4/m4a para máxima compatibilidad al reproducir.
        opts["format_sort"] = ["res", "ext:mp4:m4a"]
        opts["merge_output_format"] = "mp4"

    if args.cookies:
        opts["cookiefile"] = args.cookies
    if args.cookies_from_browser:
        opts["cookiesfrombrowser"] = (args.cookies_from_browser,)
    return opts


def normalize_url(url: str) -> str:
    url = url.strip().strip("\"'")
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url
    return url


def download(url: str, args: argparse.Namespace, outdir: Path, ffmpeg: Optional[str]) -> bool:
    try:
        import yt_dlp
        from yt_dlp.utils import DownloadError
    except ImportError:
        print("  [x] Falta la dependencia yt-dlp. Instala con: pip install yt-dlp", file=sys.stderr)
        return False

    print(f"\n  > {url}")
    try:
        with yt_dlp.YoutubeDL(build_options(args, outdir, ffmpeg)) as ydl:
            info = ydl.extract_info(url, download=True)
    except DownloadError as exc:
        msg = str(exc).replace("ERROR: ", "").strip()
        print(f"\n  [x] No se pudo descargar: {msg}", file=sys.stderr)
        low = msg.lower()
        if any(k in low for k in ("login", "private", "cookies", "sign in", "age")):
            print(
                "      Este contenido parece requerir sesion. Prueba:\n"
                '      vd0 --cookies-from-browser chrome "url"   (o firefox, edge, brave...)',
                file=sys.stderr,
            )
        else:
            print("      Si el sitio cambio, actualiza el motor con: vd0 --update", file=sys.stderr)
        return False
    except KeyboardInterrupt:
        print("\n  [!] Cancelado por el usuario.")
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"\n  [x] Error inesperado: {exc}", file=sys.stderr)
        return False

    files = _collect_paths(info)
    if files:
        for f in files:
            print(f"  [ok] Guardado en: {f}")
    else:
        print(f"  [ok] Descarga terminada en: {outdir}")
    return True


def self_update() -> int:
    print("  Actualizando el motor de descargas (yt-dlp)...")
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"]
    try:
        return subprocess.call(cmd)
    except OSError as exc:
        print(f"  [x] No se pudo actualizar: {exc}", file=sys.stderr)
        return 1


# --------------------------------------------------------------------------
# Argumentos
# --------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="vd0",
        add_help=False,
        description="Descarga videos de YouTube, Facebook, Instagram, TikTok y mas desde la terminal.",
        epilog='Ejemplo:  vd0 "https://www.youtube.com/watch?v=XXXXXXXXXXX"',
    )
    p.add_argument("urls", nargs="*", metavar="url", help="enlace(s) del video a descargar")
    p.add_argument("-a", "--audio", action="store_true", help="descargar solo el audio en MP3")
    p.add_argument(
        "-q", "--quality", choices=QUALITIES, default="best",
        help="calidad maxima de video en pixeles de alto (por defecto: best)",
    )
    p.add_argument("-o", "--output", metavar="CARPETA", help="carpeta de destino (por defecto: ~/Downloads/vd0)")
    p.add_argument("-p", "--playlist", action="store_true", help="si el enlace es una lista, descargar toda la lista")
    p.add_argument("--cookies", metavar="ARCHIVO", help="archivo cookies.txt (para contenido privado)")
    p.add_argument("--cookies-from-browser", metavar="NAVEGADOR", help="usar cookies de chrome, firefox, edge, brave, etc.")
    p.add_argument("-u", "--update", action="store_true", help="actualizar el motor de descargas (yt-dlp)")
    p.add_argument("--no-banner", action="store_true", help="no mostrar el encabezado")
    p.add_argument("-v", "--version", action="store_true", help="mostrar la version")
    p.add_argument("-h", "--help", action="store_true", help="mostrar esta ayuda")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    enable_ansi()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"vd0 {__version__}")
        return 0

    if args.help:
        print_banner()
        print(parser.format_help())
        return 0

    if args.update:
        return self_update()

    if not args.urls:
        print_banner()
        return 0

    if not args.no_banner:
        print(compact_header())

    outdir = Path(args.output).expanduser() if args.output else default_output_dir()
    try:
        outdir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"  [x] No se pudo crear la carpeta {outdir}: {exc}", file=sys.stderr)
        return 1

    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        print("  [!] No se encontro ffmpeg; algunas descargas podrian quedar sin unir audio y video.")

    ok_count = 0
    try:
        for raw in args.urls:
            if download(normalize_url(raw), args, outdir, ffmpeg):
                ok_count += 1
    except KeyboardInterrupt:
        fix_ownership(outdir)
        return 130

    fix_ownership(outdir)
    total = len(args.urls)
    if ok_count == total:
        print(f"\n  Listo: {ok_count}/{total} descarga(s) completada(s).\n")
        return 0
    print(f"\n  Terminado con errores: {ok_count}/{total} completada(s).\n", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
