# vd0

Descargador de videos para la terminal. Pega el enlace y listo: funciona con **YouTube, Facebook, Instagram, TikTok, X/Twitter, Vimeo, Reddit, Twitch** y más de 1000 sitios compatibles con [yt-dlp](https://github.com/yt-dlp/yt-dlp).

```
  10   01  1    01    0 1 0 1 0
  01   10  0 1  10  1 0     0 1 0
  ...
```

Al ejecutar `vd0` sin argumentos se muestra el nombre dibujado con números (unos y ceros), una leyenda de qué hace el programa y ejemplos de uso.

- Multiplataforma: Windows (PowerShell / CMD), Linux y macOS.
- Funciona como **usuario normal** y como **administrador** (`sudo` / PowerShell elevado).
- Incluye ffmpeg automáticamente (vía `imageio-ffmpeg`) si no lo tienes instalado.
- Sin configuración: guarda en `~/Downloads/vd0`.

## Instalación

Requiere **Python 3.8 o superior**.

### Linux y macOS

```bash
git clone https://github.com/TU_USUARIO/vd0.git
cd vd0
./install.sh            # usuario normal  -> ~/.local/bin/vd0
sudo ./install.sh       # administrador   -> /usr/local/bin/vd0 (todos los usuarios)
```

Sin clonar:

```bash
curl -fsSL https://raw.githubusercontent.com/TU_USUARIO/vd0/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
git clone https://github.com/TU_USUARIO/vd0.git
cd vd0
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1           # usuario normal; con PowerShell como administrador instala para todos
```

Sin clonar:

```powershell
irm https://raw.githubusercontent.com/TU_USUARIO/vd0/main/install.ps1 | iex
```

### Con pip / pipx

```bash
pipx install git+https://github.com/TU_USUARIO/vd0.git
# o
pip install git+https://github.com/TU_USUARIO/vd0.git
```

## Uso

```bash
vd0                                  # banner + leyenda + ayuda rápida
vd0 "https://www.youtube.com/watch?v=XXXXXXXXXXX"
vd0 -a "url"                         # solo audio (MP3)
vd0 -q 720 "url"                     # calidad máxima 720p
vd0 -o ~/Videos "url"                # carpeta de destino
vd0 -p "url_de_lista"                # descargar toda una lista
vd0 "url1" "url2" "url3"             # varios enlaces a la vez
vd0 --cookies-from-browser chrome "url"   # contenido que pide sesión
vd0 --update                         # actualizar el motor yt-dlp
vd0 -h                               # todas las opciones
```

| Opción | Descripción |
|---|---|
| `-a`, `--audio` | Descarga solo el audio en MP3 |
| `-q`, `--quality` | `best` (defecto), `2160`, `1440`, `1080`, `720`, `480`, `360` |
| `-o`, `--output` | Carpeta de destino (defecto `~/Downloads/vd0`) |
| `-p`, `--playlist` | Descarga la lista completa si el enlace es una lista |
| `--cookies ARCHIVO` | Usa un `cookies.txt` |
| `--cookies-from-browser NAV` | Usa cookies de `chrome`, `firefox`, `edge`, `brave`… |
| `-u`, `--update` | Actualiza yt-dlp |
| `--no-banner` | Oculta el encabezado |
| `-v`, `--version` | Muestra la versión |

> En PowerShell y CMD pon siempre la URL entre comillas (`"..."`), porque suele contener `&` y `?`.

### Usuario normal vs administrador

- Con `sudo vd0 "url"` los archivos se guardan en la carpeta del usuario real (no en `/root`) y se le devuelve la propiedad, así que no quedan archivos bloqueados.
- En Windows con PowerShell elevado funciona igual; la carpeta por defecto es la de tu usuario.

## Subir el proyecto a GitHub

1. Reemplaza `TU_USUARIO` por tu usuario de GitHub en `README.md`, `install.sh`, `install.ps1` y `pyproject.toml`:

   ```bash
   # Linux / macOS
   grep -rl TU_USUARIO . --exclude-dir=.git | xargs sed -i.bak 's/TU_USUARIO/tu-usuario-real/g' && find . -name '*.bak' -delete
   ```
   ```powershell
   # Windows PowerShell
   Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notmatch '\\\.git\\' } | ForEach-Object {
     (Get-Content $_.FullName -Raw) -replace 'TU_USUARIO','tu-usuario-real' | Set-Content $_.FullName -NoNewline
   }
   ```

2. Crea el repositorio y súbelo.

   **Opción A: con GitHub CLI (`gh`)**

   ```bash
   cd vd0
   git init -b main
   git add .
   git commit -m "vd0 v1.0.0: descargador de videos para terminal"
   gh auth login
   gh repo create vd0 --public --source=. --remote=origin --push
   ```

   **Opción B: manual**

   1. En https://github.com/new crea un repositorio vacío llamado `vd0` (sin README ni .gitignore).
   2. Ejecuta:

   ```bash
   cd vd0
   git init -b main
   git add .
   git commit -m "vd0 v1.0.0: descargador de videos para terminal"
   git remote add origin https://github.com/tu-usuario-real/vd0.git
   git push -u origin main
   ```

3. Publica una versión (opcional):

   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   gh release create v1.0.0 --title "vd0 v1.0.0" --notes "Primera versión"
   ```

El flujo de GitHub Actions (`.github/workflows/ci.yml`) probará la instalación en Windows, Linux y macOS en cada `push`.

## Desinstalar

```bash
# Linux / macOS (usuario)
rm -rf ~/.local/share/vd0 ~/.local/bin/vd0
# Linux / macOS (administrador)
sudo rm -rf /opt/vd0 /usr/local/bin/vd0
```
```powershell
# Windows (usuario)
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\vd0"
# Windows (administrador)
Remove-Item -Recurse -Force "$env:ProgramFiles\vd0"
```
Después elimina la entrada `...\vd0\bin` del PATH si lo deseas.

## Problemas frecuentes

| Problema | Solución |
|---|---|
| `vd0` no se reconoce | Abre una terminal nueva para que se recargue el PATH |
| Error en Instagram/Facebook/TikTok | Actualiza con `vd0 --update`; si es contenido privado usa `--cookies-from-browser chrome` |
| `externally-managed-environment` en Linux | Usa `install.sh` (crea su propio entorno virtual) |
| `No module named venv` en Debian/Ubuntu | `sudo apt install python3-venv` |

## Aviso legal

Usa vd0 únicamente con contenido propio, de dominio público o con permiso de su autor. Respeta los derechos de autor y los términos de servicio de cada plataforma; eres responsable del uso que le des.

## Licencia

MIT. Ver [LICENSE](LICENSE). El motor de descargas es [yt-dlp](https://github.com/yt-dlp/yt-dlp) (Unlicense).
