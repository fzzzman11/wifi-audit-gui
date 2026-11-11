# Contribuir a WiFi Audit Lab

Gracias por tu interés en mejorar este proyecto académico. Antes de empezar,
léete el [aviso legal](DISCLAIMER.md): cualquier contribución debe respetar el
mismo principio de **uso exclusivamente educativo y sobre redes autorizadas**.

## Requisitos previos

- Linux (el proyecto se desarrolla sobre Kali/Debian).
- Suite **aircrack-ng** e `iw` instalados (ver el [README](README.md#instalación)).
- Un adaptador WiFi con modo monitor e inyección (el laboratorio usa el
  TP-Link TL-WN722N v4, chip RTL8188EUS).
- Python **3.10 o superior**.

## Entorno de desarrollo

```bash
git clone https://github.com/TU_USUARIO/wifi-audit-gui.git
cd wifi-audit-gui

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Para ejecutar la aplicación (mantén el entorno virtual activo):

```bash
sudo -E python3 main.py
```

> El flag `-E` es necesario para que `sudo` preserve `DISPLAY`/`XAUTHORITY`
> y Qt pueda abrir la ventana. Alternativa: usar el botón "Reabrir como root"
> (pkexec) del banner inicial.

### Comprobación de estilo (lint)

El estilo se verifica con [ruff](https://docs.astral.sh/ruff/); la
configuración vive en `pyproject.toml`:

```bash
pip install -e ".[dev]"   # o simplemente: pip install ruff
ruff check .
```

El workflow [.github/workflows/lint.yml](.github/workflows/lint.yml) ejecuta
`ruff check .` en cada push y pull request. **No hay suite de tests
automatizados**: la aplicación depende de hardware inalámbrico real (modo
monitor, inyección) que no existe en los runners de CI, así que los cambios
deben verificarse manualmente en el laboratorio y describir en el PR qué se
probó y sobre qué adaptador/driver.

## Estilo de código

- **PEP 8** con líneas de **88 columnas** (compatible con el formateo de
  Black / `ruff format`).
- Type hints modernos (`str | None`) con `from __future__ import annotations`
  al inicio de cada módulo, como en el código existente.
- Docstrings y comentarios en **español**, siguiendo el tono del resto del
  proyecto.
- La capa `core/` no debe importar de `ui/`: la lógica (workers, parsers,
  herramientas) debe poder reutilizarse sin interfaz gráfica.
- Los procesos largos van en `QThread` (workers con `request_stop()`), nunca
  en el hilo principal de la UI.

## Convenciones de commits

Se sigue [Conventional Commits](https://www.conventionalcommits.org/es/):

```
<tipo>(<ámbito>): descripción breve en minúsculas y sin punto final
```

| Tipo       | Cuándo usarlo                                          |
|------------|-------------------------------------------------------|
| `feat`     | Nueva funcionalidad                                   |
| `fix`      | Corrección de un error                                 |
| `docs`     | README, DISCLAIMER, comentarios de documentación       |
| `style`    | Cambios de formato que no alteran la lógica           |
| `refactor`| Reestructuración sin cambio de comportamiento          |
| `perf`     | Mejoras de rendimiento                                 |
| `test`     | Tests (si algún día se añaden partes sin hardware)    |
| `chore`    | CI, dependencias, `.gitignore`, empaquetado           |

Ámbitos habituales: `monitor`, `scan`, `capture`, `crack`, `ui`, `tools`,
`docs`, `ci`.

Ejemplos:

```
feat(capture): pausar el deauth si el usuario detiene la captura
fix(monitor): restaurar la interfaz cuando airmon-ng falla
docs(readme): añadir troubleshooting de PyQt6 bajo Wayland
chore(ci): ejecutar ruff tambien en pull_request
```

## Flujo de trabajo con Git

1. Crea una rama desde `main`: `feature/<tema-corto>` o `fix/<issue>-<desc>`.
2. Haz commits pequeños que sigan la convención anterior.
3. Asegúrate de que `ruff check .` pasa sin errores.
4. Abre un pull request a `main` describiendo:
   - Qué cambia y por qué (referencia a la issue si existe).
   - Qué verificaste manualmente (adaptador, driver, distro).
   - Una captura de pantalla si tocas la interfaz.

## Qué no debe entrar nunca en el repositorio

- Archivos `.cap`, `.csv`, `.netxml` de capturas reales (ver el `.gitignore`
  y el [aviso legal](DISCLAIMER.md)).
- Diccionarios de contraseñas (`rockyou.txt`, etc.).
- Datos de redes de terceros (BSSIDs reales, SSIDs de vecinos, capturas con
  redes ajenas visible sin difuminar).

## Reportar problemas

Abre un issue incluyendo: distribución y versión, kernel (`uname -r`),
adaptador (`lsusb`), driver cargado (`lsmod | grep 8188`), pasos para
reproducir y la salida de error relevante. **No adjuntes capturas de redes
ajenas**: describe el problema con datos anonimizados.
