<!-- WiFi Audit Lab - README
     Cuando subas el proyecto a GitHub, sustituye "TU_USUARIO" por tu
     usuario real en: badges, enlaces de clonacion y tabla de creditos. -->

<div align="center">

# ◈ WiFi Audit Lab

**Laboratorio GUI (PyQt6) para el estudio guiado del flujo de auditoría WPA/WPA2 con la suite aircrack-ng: modo monitor → escaneo → captura de handshake → crackeo por diccionario.**

Proyecto académico para un laboratorio universitario de ciberseguridad.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52?logo=qt&logoColor=white)
![aircrack-ng](https://img.shields.io/badge/backend-aircrack--ng-0E4B8F)
![Licencia](https://img.shields.io/badge/licencia-GPLv3-blue)
![Lint](https://github.com/TU_USUARIO/wifi-audit-gui/actions/workflows/lint.yml/badge.svg)

</div>

> [!WARNING]
> **Uso exclusivamente educativo.** Esta herramienta está pensada para prácticas
> de laboratorio sobre **redes propias o autorizadas**. Capturar handshakes,
> enviar paquetes de desautenticación o probar diccionarios contra redes de
> terceros sin autorización expresa puede constituir un delito. Consulta el
> aviso completo en [DISCLAIMER.md](DISCLAIMER.md).

---

<!-- CAPTURA DE PANTALLA (placeholder)
     1. Ejecuta la app:  sudo -E python3 main.py
     2. Haz capturas de cada pantalla y guárdalas en docs/images/:
          docs/images/main_window.png    (ventana principal completa)
          docs/images/interface_page.png (paso 1 · interfaz)
          docs/images/scan_page.png       (paso 2 · tabla de redes)
          docs/images/capture_page.png    (paso 3 · captura en curso)
          docs/images/analysis_page.png   (paso 4 · aircrack-ng)
        Puedes usar, por ejemplo:
          gnome-screenshot -w -f docs/images/main_window.png
          flameshot gui
     3. Descomenta el bloque <img> de abajo para la captura principal
        (ya apunta a docs/images/main_window.png) y añade los demás
        en cada paso de la sección "Uso".
     4. Recorte recomendado: sin barra de título; difumina BSSIDs/SSIDs
        de redes ajenas que aparezcan por accidente.
-->
<p align="center">
  <em>📷 Placeholder · guarda la ventana principal como
  <code>docs/images/main_window.png</code> y descomenta el bloque
  <code>&lt;img&gt;</code> del código fuente de este README.</em>
</p>

<!--
<p align="center">
  <img src="docs/images/main_window.png" alt="Ventana principal de WiFi Audit Lab" width="900">
</p>
-->

## Tabla de contenidos

1. [Sobre el proyecto](#sobre-el-proyecto)
2. [Características](#características)
3. [Flujo de trabajo](#flujo-de-trabajo)
4. [Requisitos](#requisitos)
5. [Instalación](#instalación)
6. [Uso](#uso)
7. [Archivos generados](#archivos-generados)
8. [Solución de problemas](#solución-de-problemas)
   - [Driver RTL8188EU / RTL8188EUS](#driver-rtl8188eu--rtl8188eus)
   - [Problemas de PyQt6](#problemas-de-pyqt6)
9. [Estructura del proyecto](#estructura-del-proyecto)
10. [Empaquetado opcional (pip)](#empaquetado-opcional-pip)
11. [Desarrollo](#desarrollo)
12. [Hoja de ruta](#hoja-de-ruta)
13. [Licencia](#licencia)
14. [Créditos](#créditos)

## Sobre el proyecto

WiFi Audit Lab es un **proyecto académico** desarrollado para una asignatura de
ciberseguridad. Su propósito es didáctico: en lugar de teclear a mano la cadena
de comandos de aircrack-ng, la aplicación guía al alumno por las cuatro fases
de una auditoría WPA/WPA2 en un entorno controlado, mostrando en cada paso qué
herramienta se lanza, con qué argumentos y qué produce.

| Fase | Pantalla | Herramienta | Qué ocurre | Qué se aprende |
|------|----------|-------------|------------|----------------|
| 1 | Interfaz | `airmon-ng` | El adaptador pasa de *managed* a *monitor* | Qué es el modo monitor y por qué se necesita |
| 2 | Escaneo | `airodump-ng` | Se enumeran redes (ESSID, BSSID, canal, cifrado, señal) | Cómo se anuncian los APs y cómo se leen con airodump-ng |
| 3 | Captura | `airodump-ng` + `aireplay-ng` | Captura dirigida del 4-way handshake; el deauth (10 paquetes) es opcional y exige confirmación | Cómo funciona la autenticación WPA/WPA2 (el handshake) |
| 4 | Análisis | `aircrack-ng` | Se prueba un diccionario contra el handshake capturado | Por qué una contraseña débil cae ante un ataque de diccionario |

## Características

- Asistente en **4 pasos** con barra lateral de navegación y badges de estado
  (ROOT, MONITOR).
- **Diálogo legal obligatorio** al arrancar: hay que confirmar que se dispone
  de autorización antes de usar la aplicación.
- Workers en hilos (`QThread`): la interfaz nunca se congela durante escaneos,
  capturas o crackeos, y todo puede detenerse con **DETENER TODO**.
- Comprobación automática al inicio de privilegios root y de las herramientas
  del sistema requeridas.
- Al salir, la interfaz se **restaura a modo managed** y se reinicia
  NetworkManager automáticamente.
- Capturas con nombre descriptivo en `~/wifi_audit_capturas/` para adjuntarlas
  fácilmente al informe de laboratorio.

## Flujo de trabajo

```
+--------------+     +--------------+     +------------------------+     +---------------------+
| 1. INTERFAZ  | --> | 2. ESCANEO   | --> | 3. CAPTURA             | --> | 4. ANALISIS         |
| airmon-ng    |     | airodump-ng  |     | airodump-ng dirigido,  |     | aircrack-ng con un  |
| modo monitor |     | bandas 2.4 y |     | handshake + deauth     |     | diccionario contra  |
|              |     | 5 GHz        |     | opcional (10 paquetes) |     | el handshake (.cap) |
+--------------+     +--------------+     +------------------------+     +---------------------+
```

## Requisitos

### Hardware

- Adaptador WiFi que soporte **modo monitor e inyección**. Probado en el
  laboratorio con el **TP-Link TL-WN722N v4** (chip Realtek **RTL8188EUS**),
  que necesita un driver concreto: ver
  [Driver RTL8188EU / RTL8188EUS](#driver-rtl8188eu--rtl8188eus).
- La tarjeta WiFi interna de la mayoría de portátiles **no sirve** para estas
  prácticas.

### Software

- Linux (desarrollado y probado en Kali / Debian).
- Suite [aircrack-ng](https://www.aircrack-ng.org/) e `iw`.
- Python **3.10+** y **PyQt6 ≥ 6.5**.

## Instalación

### Kali Linux (recomendado para el laboratorio)

Kali ya incorpora la suite aircrack-ng; solo faltan piezas sueltas:

```bash
sudo apt update
sudo apt install aircrack-ng iw python3-venv
```

### Debian / Ubuntu

```bash
sudo apt update
sudo apt install aircrack-ng iw python3 python3-venv python3-pip
```

### Arch Linux

```bash
sudo pacman -S aircrack-ng iw python
```

### Driver RTL8188EUS (TP-Link TL-WN722N v4 y otros adaptadores RTL8188EU)

El driver genérico del kernel (`r8188eu`) no soporta bien el modo monitor ni
la inyección. Si tu adaptador usa este chip, instala primero el driver
mantenido por aircrack-ng: sigue la guía de
[Driver RTL8188EU / RTL8188EUS](#driver-rtl8188eu--rtl8188eus).

### Entorno Python

```bash
git clone https://github.com/fzzzman11/wifi-audit-gui.git
cd wifi-audit-gui
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

Ejecuta siempre con `-E` para que `sudo` preserve las variables de entorno de
gráficos (`DISPLAY`, `XAUTHORITY`) y Qt pueda abrir la ventana:

```bash
sudo -E python3 main.py
```

Alternativa: abrir la app como usuario normal y pulsar **"Reabrir como root"**
en el banner (usa `pkexec`, que ya preserva el entorno gráfico).

1. **Diálogo legal.** Lee las condiciones, marca la casilla de confirmación de
   autorización y pulsa *Aceptar y continuar*. Sin ese paso la aplicación no
   se abre.
2. **Paso 1 · Interfaz.** Selecciona tu adaptador (p. ej. `wlan0`) y pulsa
   *Activar modo monitor*. El badge de la cabecera pasará a
   `MONITOR · wlan0mon`.
3. **Paso 2 · Escaneo.** Elige duración y banda (2.4 GHz / 5 GHz) y lanza el
   escaneo. Las redes detectadas aparecen en una tabla: ESSID, BSSID, canal,
   cifrado, clientes y señal. Selecciona tu red de prácticas y pulsa
   *Capturar handshake*.
4. **Confirmación de objetivo.** La aplicación muestra los datos de la red
   (SSID, BSSID, canal) y exige confirmar que es tuya o que tienes
   autorización. El envío de **deauth** (10 paquetes con `aireplay-ng` para
   forzar la reconexión de un cliente) es opcional con casilla.
5. **Paso 3 · Captura.** Panel de estado en vivo: clientes detectados, paquetes
   y tiempo transcurrido. Al aparecer el handshake, la app pita, muestra la
   ruta del `.cap` y habilita el análisis.
6. **Paso 4 · Análisis.** Selecciona el diccionario del laboratorio y lanza
   `aircrack-ng`. Se muestra el progreso (claves probadas, claves/s) y el
   resultado: la clave encontrada o "no está en el diccionario".
7. **Al salir.** La app detiene los procesos, restaura la interfaz a modo
   *managed* y reinicia NetworkManager.

> [!TIP]
> En el laboratorio genera el handshake de forma natural conectando y
> desconectando un cliente de la red de pruebas antes de recurrir al deauth:
> es más limpio y no interrumpe la conectividad de otros clientes.

## Archivos generados

Por defecto, la aplicación escribe en `~/wifi_audit_capturas/`:

```
~/wifi_audit_capturas/
└── handshake_<ESSID>_<AAAAMMDD_HHMMSS>-01.cap   (+ .csv y .netxml de airodump-ng)
```

Los `.cap` contienen material de autenticación de la red auditada: **no los
subas ni compartas** (el `.gitignore` los excluye del repositorio). Puedes
vaciar la carpeta al terminar la práctica con
`rm -rf ~/wifi_audit_capturas`.

## Solución de problemas

### Driver RTL8188EU / RTL8188EUS

**Síntoma típico:** `airmon-ng` no crea la interfaz monitor, o el test de
inyección falla (`Injection: 0/30`).

**Causa:** el kernel carga el driver genérico `r8188eu`, que no soporta
completamente el modo monitor ni la inyección de paquetes.

**Solución:** compilar el driver mantenido por el equipo de aircrack-ng y
bloquear el genérico:

```bash
sudo apt install -y git build-essential dkms linux-headers-$(uname -r)
git clone https://github.com/aircrack-ng/rtl8188eus.git
cd rtl8188eus
make
sudo make install
echo "blacklist r8188eu" | sudo tee /etc/modprobe.d/blacklist-r8188eu.conf
sudo reboot
```

Verificación tras reiniciar:

```bash
iw phy | grep -i monitor           # debe aparecer "* monitor"
sudo airmon-ng start wlan0
sudo aireplay-ng --test wlan0mon  # debe decir "Injection is working!"
```

Otros errores habituales del adaptador y del flujo de auditoría:

| Error / síntoma | Causa probable | Solución |
|---|---|---|
| `SIOCSIFFLAGS: Operation not possible due to RF-kill` | WiFi bloqueado por rfkill | `sudo rfkill unblock all` |
| `Device or resource busy (-16)` al activar el monitor | NetworkManager / wpa_supplicant retienen la interfaz | `sudo airmon-ng check kill` y reintenta |
| `aireplay-ng --test` → `Injection: 0/30` | Driver genérico sin soporte de inyección | Instala `rtl8188eus` (ver arriba) y recoloca el adaptador USB |
| No aparece `wlan0` en la app | Driver no cargado o USB no enumerado | `lsusb` y `dmesg \| grep -i 8188`; reconecta el adaptador |
| Tras usar la app, el WiFi del equipo no funciona | NetworkManager quedó detenido | `sudo systemctl restart NetworkManager` |
| El modo monitor "se cae" solo | El gestor de red reclama la interfaz | Detén NetworkManager durante la práctica: `sudo systemctl stop NetworkManager` |
| El handshake nunca llega | Cliente lejos, canal cambiante o AP sin clientes | Acércate al AP, asegúrate de que hay un cliente conectado, activa el deauth |
| `Could not read MAC from IP` / interfaz rara tras varias prácticas | Estado residual del driver | `sudo rmmod 8188eu && sudo modprobe 8188eu` (o reinicia) |

### Problemas de PyQt6

| Error / síntoma | Causa probable | Solución |
|---|---|---|
| `qt.qpa.plugin: Could not load the Qt platform plugin "xcb"` | Faltan librerías X11 de Qt en el sistema | Debian/Kali: `sudo apt install libxkbcommon-x11-0 libxcb-cursor0 libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0` · Arch: `sudo pacman -S libxkbcommon-x11` |
| `ImportError: libGL.so.1: cannot open shared object file` | Falta la librería de OpenGL/Mesa | `sudo apt install libgl1` |
| La ventana no abre al ejecutar con `sudo python3 main.py` | `sudo` pierde `DISPLAY` / `XAUTHORITY` | Usa `sudo -E python3 main.py` o el botón *Reabrir como root* (pkexec) |
| Pantalla en negro o cuelgues bajo Wayland | Plugin wayland inestable | `QT_QPA_PLATFORM=xcb sudo -E python3 main.py` |
| `ModuleNotFoundError: No module named 'PyQt6'` | Entorno virtual sin activar o sin el paquete | `source .venv/bin/activate && pip install -r requirements.txt` |
| Fuentes o iconos raros cuando corre como root | `root` usa otro `$HOME` y otro tema Qt | Es cosmético; puede fijarse un tema con Qt, pero no afecta a la práctica |

## Estructura del proyecto

```
wifi-audit-gui/
├── main.py                    # Punto de entrada: diálogo legal + ventana principal
├── core/                      # Lógica de la aplicación (sin dependencias de la UI)
│   ├── constants.py           #   constantes: nombre, versión, rutas, herramientas
│   ├── process.py             #   ejecución de comandos con PTY (para \r de aircrack)
│   ├── tools.py               #   detección de root, herramientas e interfaces
│   ├── monitor.py             #   workers: activar/restaurar modo monitor
│   ├── scanner.py             #   worker: escaneo con airodump-ng
│   ├── capture.py             #   worker: captura dirigida + deauth opcional
│   ├── cracker.py             #   worker: aircrack-ng con diccionario
│   └── parsers.py             #   parseo de la salida de las herramientas
├── ui/                        # Interfaz (PyQt6)
│   ├── legal_dialog.py        #   aviso legal obligatorio al arrancar
│   ├── main_window.py         #   orquestación de páginas, workers y estado
│   ├── theme.py               #   hoja de estilos QSS (tema oscuro)
│   ├── widgets.py             #   widgets reutilizables (cards, badges)
│   └── pages/                #   las 4 pantallas del asistente
├── docs/images/               # Capturas de pantalla del README
├── .github/workflows/lint.yml # CI: ruff en cada push/PR
├── pyproject.toml             # Metadatos + configuración de ruff
├── requirements.txt           # Dependencias de ejecución (PyQt6)
├── DISCLAIMER.md              # Aviso legal y ético extendido
├── CONTRIBUTING.md            # Guía de desarrollo y convenciones
└── LICENSE                    # GPLv3
```

## Empaquetado opcional (pip)

**Recomendación para este proyecto: no es necesario publicarlo como paquete
pip.** La aplicación necesita privilegios root, las herramientas del sistema
(aircrack-ng, iw) y hardware inalámbrico real, así que el flujo natural del
laboratorio es clonar el repositorio, crear un venv y ejecutar
`sudo -E python3 main.py` desde el código.

Aun así, el `pyproject.toml` incluido deja el proyecto preparado por si
interesara instalarlo (`pip install .` crearía el comando `wifi-audit-lab`):

```bash
pip install .
wifi-audit-lab            # como usuario normal (solo exploración de la UI)
sudo $(which wifi-audit-lab)   # con root, para el flujo completo
```

También centraliza los metadatos del proyecto y la configuración de `ruff` que
usa el workflow de CI.

## Desarrollo

Las instrucciones para montar el entorno de desarrollo, las convenciones de
commits (Conventional Commits) y el proceso de pull requests están en
[CONTRIBUTING.md](CONTRIBUTING.md).

```bash
git clone https://github.com/fzzzman11/wifi-audit-gui.git
cd wifi-audit-gui
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ruff check .    # misma verificación que ejecuta el CI
```

## Hoja de ruta

- [ ] Exportar el handshake al formato 22000 para poder usar `hashcat`.
- [ ] Captura PMKID sin necesidad de cliente asociado (donde el AP lo permita).
- [ ] Documentar otros adaptadores de laboratorio probados (además del
      TL-WN722N v4).
- [ ] Panel de informe: resumen de la sesión para adjuntar al documento del
      laboratorio.

## Licencia

Este proyecto se distribuye bajo la **Licencia Pública General GNU v3
(GPLv3)**. Consulta el texto completo en [LICENSE](LICENSE).

El código se comparte con fines educativos; cualquier obra derivada que se
distribuya debe mantenerse abierta bajo la misma licencia. Las condiciones de
uso ético y legal se detallan en [DISCLAIMER.md](DISCLAIMER.md), que forma
parte de la documentación del proyecto y debe leerse antes de ejecutar la
aplicación.

## Créditos

Proyecto académico desarrollado por **[F.N.D]**

- Interfaz y automatización: WiFi Audit Lab.
- Motor de auditoría: la suite [aircrack-ng](https://www.aircrack-ng.org/),
  driver RTL8188EUS de
  [aircrack-ng/rtl8188eus](https://github.com/aircrack-ng/rtl8188eus).
