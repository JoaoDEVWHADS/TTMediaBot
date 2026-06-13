# TTMediaBot

**¡Hola! Soy João Almeida.** Bienvenido a mi fork de **TTMediaBot**, un bot completo de transmisión de música y medios para TeamTalk 5. Este repositorio está enfocado en ofrecer mejoras constantes, estabilidad y nuevas características, como el soporte exclusivo para YouTube Music.

> 🔗 **Mi Repositorio:** [https://github.com/JoaoDEVWHADS/TTMediaBot](https://github.com/JoaoDEVWHADS/TTMediaBot)

---

> **Nota:** Este repositorio es un fork del [TTMediaBot original](https://github.com/gumerov-amir/TTMediaBot).

Un bot de streaming de medios completo para TeamTalk 5, capaz de reproducir música desde varios servicios (YouTube, YouTube Music, archivos locales, URLs) con funciones de control avanzadas.


## 📋 Diferencias con el Original

Este fork incluye varias modificaciones y optimizaciones:

- **Servicios Eliminados:** Se eliminó la integración con Yandex Music y VK.
- **Actualización del SDK de TeamTalk:** Actualizado a la versión 5.8.1 para un mejor rendimiento.
- **Soporte para Arquitectura ARM64:** Se añadió soporte nativo para ARM64 (como Raspberry Pi y servidores AWS Graviton) con detección automática de plataforma y descarga de librerías durante la instalación.
  > [!NOTE]
  > En sistemas `x86_64`, la instalación se mantiene mínima y sin cambios. En sistemas `ARM`, el instalador y el Dockerfile instalan de manera condicional las dependencias adicionales (como `libportaudio2`) requeridas por la versión ARM del SDK de TeamTalk.
- **Soporte para Distribuciones Linux Universal:** El instalador (`ttbotdocker.sh` / `install_git_clone.sh`) ahora soporta de forma dinámica la configuración automática de Docker y dependencias en cualquier distribución principal (Ubuntu, Debian, CentOS, RHEL, Fedora, Rocky Linux, AlmaLinux, Raspbian, Arch, etc.) usando el instalador oficial universal y fallbacks de administradores de paquetes para `jq`.
- **Contenedores Docker:** El bot se ejecuta en contenedores Docker basados en Debian 11 y Python 3.10, asegurando la compatibilidad con dependencias heredadas y manteniendo la estabilidad.
- **Estabilidad Comprobada:** Desde que conocí este bot en 2021, las adaptaciones realizadas para evadir las restricciones de YouTube, combinadas con las optimizaciones de 2021/2022, han demostrado ser excelentes y confiables.

## 🆕 Últimas Actualizaciones

Para ver el historial completo de cambios, incluyendo todas las nuevas funciones, correcciones de errores y optimizaciones, por favor consulta el changelog.

> 📋 **[Ver changelog completo →](CHANGELOG.md)**


## 🎵 Soporte para YouTube Music

Este fork incluye soporte optimizado para **YouTube Music** junto con el YouTube estándar:

- **Integración con la API de Búsqueda de YouTube:** Utiliza la API de Búsqueda de YouTube para una búsqueda de música rápida y confiable.
- **Librerías Optimizadas:** 
  - YouTube utiliza `py-yt-search`: una librería de Python rápida y moderna para búsquedas en YouTube.
  - YouTube Music utiliza `ytmusicapi`: la librería oficial de la API de YouTube Music.
  - Ambos servicios utilizan `yt-dlp` para la extracción de audio.
- **Enfoque en el Rendimiento:** Diseñado para ejecutarse con los mínimos cuellos de botella, garantizando una reproducción fluida y resultados de búsqueda rápidos.
- **Sistema Unificado de Cookies:** Tanto YouTube como YouTube Music comparten la misma configuración de cookies para la autenticación.
- **📦 Descarga de Listas de Reproducción y Álbumes:** Soporte completo para descargar colecciones completas mediante el comando `dlp` con nombres inteligentes basados en metadados.
- **🕵️ Progresso en Tiempo Real por Mensaje Privado (PV):** Mantente al tanto de tus descargas sin saturar el chat del canal.

Cambia entre servicios usando el comando `sv`:
- `sv yt` - Cambiar a YouTube
- `sv ytm` - Cambiar a YouTube Music

> [!NOTE]
> **Función Exclusiva:** El soporte para YouTube Music es exclusivo de este fork y no está disponible en el proyecto TTMediaBot original.

## 🔗 Descarga basada en enlaces y almacenamiento local

Este fork incluye un sistema avanzado de descarga basado en enlaces que permite a los usuarios encolar enlaces de medios, listarlos, gestionarlos y descargarlos de forma secuencial o en archivos comprimidos.

### Comandos
- **`aad [enlace]`**: Añade un único enlace a tu lista de descargas.
- **`ad [enlace1] [enlace2] ...`**: Añade múltiples enlaces separados por espacio a tu lista.
- **`ld`**: Lista todos los enlaces actualmente en tu lista.
- **`rd [número/enlace]`**: Elimina un enlace de tu lista por índice o URL.
- **`ldd [enlace]`**: Descarga un enlace directamente y lo sube al canal.
- **`ads`**: Descarga tu lista. Te permite seleccionar:
  - **Opción 1 (Normal):** Descarga cada pista individualmente y la sube al canal.
  - **Opción 2 (ZIP):** Resuelve y comprime todas las pistas en un único archivo ZIP, y luego lo sube al canal.
- **`adsc`**: Alterna el **modo de descarga local** (volátil). Cuando está activo:
  - Las pistas de la lista `ads` se guardan directamente en el sistema de archivos del VPS en lugar de subirse a TeamTalk.
  - La Opción 1 guarda los archivos en `data/Downloads/music/` (host: `bots/nombre_bot/Downloads/music/`).
  - La Opción 2 guarda los archivos ZIP en `data/Downloads/zips/` (host: `bots/nombre_bot/Downloads/zips/`).
  - Los archivos guardados localmente nunca se eliminan de forma automática.
  - Muestra un reporte final de éxito/error al finalizar.

## 🚀 Instalación Fácil (Recomendado)

Este script instalará automáticamente Git (si es necesario), clonará el repositorio y configurará el entorno Docker.

1.  **Descarga y ejecuta el instalador:**
    ```bash
    wget https://raw.githubusercontent.com/JoaoDEVWHADS/TTMediaBot/master/install_git_clone.sh
    sudo chmod +x install_git_clone.sh
    sudo ./install_git_clone.sh
    ```

2.  **Monitorea la terminal:**
    *   El script instalará automáticamente todas las dependências (incluido Docker si es necesario).
    *   Presta atención a la salida de la terminal para seguir el progreso de la instalación.
    *   Puedes administrar múltiples bots, actualizar el código y cambiar configuraciones a través del administrador de Docker.

---

## ⚙️ Configuración Manual

Si necesitas editar manualmente las configuraciones del bot después de la instalación:

1. Los **archivos de configuración** se encuentran en el directorio `bots` dentro de la carpeta `TTMediaBot` después de la configuración inicial.
2. **Realiza tus cambios** en los archivos de configuración según sea necesario.
3. **Reinicia el bot** usando uno de estos métodos:
   - **Vía script de Docker:** Ejecuta `./ttbotdocker.sh`, selecciona la opción `2` (Manage Bots) y luego elige la opción de reiniciar (usualmente la opción `2`).
   - **Vía comando de bot:** Envía `rs` como mensaje privado al bot (requiere privilegios de administrador).

---

## 🎮 Comandos

Envía estos comandos al bot mediante mensaje privado (PV) o en el canal (si está habilitado).

### Comandos de Usuario
| Comando | Argumentos | Descripción |
| :--- | :--- | :--- |
| **h** | | Muestra la ayuda de los comandos. |
| **p** | `[búsqueda]` | Reproduce pistas encontradas para la búsqueda. Si no hay argumento, pausa/reanuda. |
| **u** | `[url]` | Reproduce una transmisión/archivo desde una URL directa. |
| **s** | | Detiene la reproducción. |
| **n** | | Reproduce la siguiente pista. |
| **b** | | Reproduce la pista anterior. |
| **v** | `[0-100]` | Ajusta el volumen. Sin argumento muestra el nivel de volumen actual. |
| **sb** | `[segundos]` | Retrocede en la reproducción. Paso por defecto si no hay argumento. |
| **sf** | `[segundos]` | Avanza en la reproducción. Paso por defecto si no hay argumento. |
| **c** | `[número]` | Selecciona una pista por número desde los resultados de búsqueda. |
| **m** | `[modo]` | Define el modo de reproducción: `SingleTrack`, `RepeatTrack`, `TrackList`, `RepeatTrackList`, `Random`. |
| **sp** | `[0.25-4]` | Define la velocidad de reproducción. |
| **sv** | `[servicio]` | Cambia de servicio (ej: `sv yt`, `sv ytm`). |
| **f** | `[+/-][num]` | Gestión de Favoritos. `f` lista. `f +` añade la actual. `f -` elimina. `f [num]` reproduce. |
| **gl** | | Obtiene el enlace directo a la pista actual. |
| **dl** | | Descarga la pista actual y la sube al canal. |
| **dlv** | | Descarga la pista actual como video y la sube al canal. |
| **dlp** | `[url]` | Descarga todas las pistas de una lista de reproducción/álbum de YouTube, las comprime en ZIP y las sube al canal. |
| **aad** | `[enlace]` | Añade un único enlace/URL a tu lista de descargas personalizada. |
| **ad** | `[enlaces]` | Añade múltiples enlaces separados por espacio a la lista de descargas. |
| **ld** | | Lista todos los enlaces actualmente en la lista de descargas. |
| **rd** | `[número/enlace]` | Elimina un enlace de la lista de descargas por índice o URL. |
| **ldd** | `[enlace]` | Descarga un enlace directamente y lo sube al canal de TeamTalk. |
| **ads** | `[1/2]` | Descarga la lista: Opción 1 (Normal secuencial) o Opción 2 (ZIP comprimido). |
| **adsc** | | Alterna el modo de descarga local: guarda los archivos localmente en el VPS en vez de subirlos. |
| **r** | `[número]` | Reproduce desde Recientes. `r` lista los recientes. |
| **jc** | | Hace que el bot se una a tu canal actual. |
| **qa** | `[búsqueda]` | Añade una pista a la cola de reproducción. |
| **ql** | | Lista todas las pistas actualmente en la cola. |
| **qr** | `[número]` | Elimina una pista específica de la cola. |
| **qc** | | Limpia toda la cola de reproducción. |
| **qs** | | Salta la pista actual y reproduce la siguiente de la cola de inmediato. |
| **sr** | `[on/off]` | Alterna el Modo de Resultados de Búsqueda. Cuando está activo, `p BÚSQUEDA` muestra una lista numerada en lugar de reproducir inmediatamente. Guarda con `sc`. |
| **sl** | `[número]` | Selecciona y reproduce el resultado NÚMERO de la última búsqueda con el modo `sr` activo. |
| **slc** | `[número]` | Establece cuántos resultados se muestran en el modo `sr` (por defecto 5). Sin argumento muestra el conteo actual. |
| **a** | | Muestra información sobre el bot. |

### Comandos de Administrador
*Requiere privilegios de administrador definidos en `config.json`.*

| Comando | Argumentos | Descripción |
| :--- | :--- | :--- |
| **cg** | `[n/m/f]` | Cambia el género del bot (neutro, masculino, femenino). |
| **cl** | `[código]` | Cambia el idioma (ej: `en`, `ru`, `pt_BR`). |
| **cn** | `[nombre]` | Cambia el apodo del bot. |
| **cs** | `[texto]` | Cambia el texto de estado del bot. |
| **cc** | `[r/f]` | Limpia el caché (`r`=recientes, `f`=favoritos). |
| **cm** | | Alterna el envío de mensajes al canal. |
| **ajc** | `[id] [contraseña]`| Fuerza la entrada a un canal por ID. |
| **bc** | `[+/-cmd]` | Bloquea/Desbloquea un comando. |
| **l** | | Bloquea/Desbloquea el bot (solo admins pueden usarlo). |
| **ua** | `[+/-user]` | Añade/Elimina usuarios administradores. |
| **ub** | `[+/-user]` | Añade/Elimina usuarios baneados. |
| **eh** | | Alterna el procesamiento de eventos internos. |
| **sc** | | Guarda la configuración actual en el archivo. |
| **va** | | Alterna la transmisión de voz. |
| **rs** | | Reinicia el bot. |
| **q** | | Apaga/Cierra el bot. |
| **gcid** | | Obtiene el ID del canal actual. |

---

## 🐳 Script de Gestión de Docker (`ttbotdocker.sh`)

El script `ttbotdocker.sh` es una herramienta integral de administración para el TTMediaBot. Proporciona una interfaz basada en menús para manejar todos los aspectos de despliegue y control de bots.

### Opciones del Menú Principal

#### 1. Crear Bot
Crea una nueva instancia de bot con un asistente de configuración completo:
- **Nombre del bot:** Nombre del contenedor y de la carpeta.
- **Configuración del servidor:** Dirección del servidor, puertos TCP/UDP, cifrado.
- **Credenciales:** Usuario y contraseña.
- **Cookies:** Ruta hacia el archivo de cookies de YouTube.
- **Creación en lote:** Crea múltiples bots de una vez con numeración automática:
  - Detecta automáticamente números de bots existentes y continúa la secuencia.
  - Nombres separados para contenedores y apodos.
  - Evita conflictos en el mismo servidor TeamTalk.

#### 2. Gestionar Bots
Submenú completo de administración de bots con 12 opciones:

**2.1. Iniciar Todos los Bots**
- Inicia todos los contenedores de bots detenidos.
- Usa filtrado por etiquetas de Docker (`role=ttmediabot`).

**2.2. Reiniciar Todos os Bots**
- Detiene todos los bots (tiempo límite de 1 segundo).
- Los inicia nuevamente de inmediato.
- Útil para aplicar cambios de configuración.

**2.3. Detener Todos los Bots**
- Detiene de forma limpia todos los bots en ejecución (tiempo límite de 1 segundo).

**2.4. Eliminar Bot**
- Menú interactivo para seleccionar y eliminar un único bot.
- Mostra una lista numerada de todos los bots.
- Elimina tanto el contenedor como la carpeta de configuración.
- Requiere confirmación antes de la eliminación.

**2.5. Eliminación en Lote de Bots**
- Elimina múltiples bots en una sola operación.
- Introduce números separados por espacio (ej: `1 3 5`).
- Usa la opción `0` para **eliminar TODOS los bots** simultáneamente.
- Muestra un resumen antes del borrado para una eliminación eficiente y paralela.

**2.6. Duplicar Bot**
- Clona la configuración de un bot existente.
- Selecciona el bot de origen desde la lista numerada.
- Muestra la dirección del servidor para cada bot.
- Soporte para duplicación en lote (crear múltiples copias).
- Numeración automática de contenedores y solicita el **PREFIJO DEL APODO**.
- Detención inteligente de conflictos: evita la clonación si el nombre base ya existe.

**2.7. Actualizar Cookies (Todos los Bots)**
- Actualiza las cookies de YouTube para todos los bots de una vez.
- Copia el nuevo archivo de cookies a todas las carpetas de bots.
- Reinicia automáticamente todos los bots para aplicar los cambios.
- Define los permisos correctos del archivo (1000:1000).

**2.8. Reiniciar con Temporizador**
- Detiene todos los bots, espera el tiempo especificado y luego los inicia.
- Útil para mantenimiento coordinado del servidor.
- Cronómetro visual de cuenta regresiva.
- Tiempo especificado en segundos.

**2.9. Actualización de Configuración en Lote**
- Actualiza la configuración para todos los bots simultáneamente.
- Elige qué actualizar:
  1. Servidor (hostname)
  2. Puertos (TCP/UDP)
  3. Cifrado
  4. Credenciales (usuario/contraseña)
  5. Todo
- Muestra la configuración actual del primer bot.
- Vista previa de cambios antes de aplicar.
- Actualiza todos los archivos `config.json` de los bots.

> [!WARNING]
> **Importante:** Esta característica está diseñada para bots en el **mismo servidor**. Si tienes bots conectados a varios servidores TeamTalk diferentes, tendrás que actualizarlos manualmente. El uso de esta opción configurará todos los bots con los mismos ajustes de servidor.

**2.10. Backup / Restauración de Bots**
- Utilidad portátil de respaldo/restauración para la configuración y caché de los bots.
- Guarda respaldos comprimidos (`.tar.gz`) en un directorio `backups/`.
- La restauración redespliega dinámicamente las configuraciones y recrea los contenedores Docker.

**2.11. Limpiar Todos los Logs de los Bots**
- Utilidad de limpieza rápida que elimina todos los archivos `*.log` de todas las carpetas de datos de los bots para liberar espacio en disco.

**2.12. Volver al Menú Principal**

#### 3. Reconstruir Imagen / Actualizar Código
Actualiza el código del bot y reconstruye la imagen de Docker:
- Reconstruye la imagen Docker con `CACHEBUST` para garantizar código nuevo.
- Recria los contenedores con la nueva imagen.
- Reinicia solo los bots que estaban corriendo previamente.

#### 4. Desinstalar Todo
Limpieza completa de la instalación de TTMediaBot:
- Detiene todos los contenedores de bots.
- Elimina todos los contenedores.
- Borra todas las carpetas de bots.
- Remueve la imagen de Docker.
- **Advertencia:** ¡Esta acción es irreversible!

#### 5. Verificar Actualizaciones
Verifica automáticamente si hay actualizaciones en el repositorio de GitHub.
- Usa `update.sh` para comparar el código local con el repositorio remoto.
- Realiza una copia de seguridad segura de la configuración antes de actualizar.
- Incluye una pausa al final para que los usuarios puedan leer la salida del terminal.

#### 6. Activar/Desactivar Actualizaciones Automáticas
Menú dedicado para alternar las actualizaciones automáticas en segundo plano mediante systemd.

#### 7. Limpiar Caché de Docker
Herramienta de limpieza avanzada para recuperar espacio en disco sin afectar los bots en ejecución:
- **Docker Prune:** Elimina contenedores detenidos e imágenes no utilizadas.
- **Buildx Cleanup:** Limpia la caché de construcción persistente.
- **Logs del Sistema:** Limpia logs de `journalctl` con más de 1 día de antigüedad.
- **Huella Cero:** Garantiza que el sistema host permanezca limpio.

#### 8. Salir
Cierra el script.

### Características Automáticas

El script hace automáticamente:
- **Verificación de actualizaciones** en el arranque si `update.sh` está presente.
- **Instalación de dependencias** (Docker, jq) en la primera ejecución.
- **Construcción de la imagen Docker** automáticamente y fuerza a PIP a actualizar las librerías (`-U`) en cada reconstrucción.
- **Sin prompts al inicio:** La reconstrucción ahora es una opción de menú manual (Opción 3), agilizando el arranque.
- **Crea la estructura del directorio** `bots`.
- **Detecta conflictos** (nombres de contenedores, apodos en el mismo servidor).
- **Define los permisos** correctos para los volúmenes de Docker.
- **Usa etiquetas** para una fácil filtración de contenedores.

---

## 🔄 Script de Actualización Independiente (`update.sh`)

Si ya tienes los bots instalados y solo deseas actualizar el código sin usar el administrador de Docker completo, puedes utilizar el script independiente `update.sh`.

**Cómo usar:**
1. Descarga el script a tu carpeta `TTMediaBot`:
   ```bash
   wget https://raw.githubusercontent.com/JoaoDEVWHADS/TTMediaBot/master/update.sh
   chmod +x update.sh
   ```
2. Ejecútalo:
   ```bash
   sudo ./update.sh
   ```

Este script actualizará el repositorio, reconstruirá la imagen y recreará los contenedores, garantizando que todo esté al día.

---

## 🍪 Configuración de Cookies de YouTube & YouTube Music

Las cookies son **esenciales** para que el bot reproduzca música de **YouTube** y de **YouTube Music** debido a restricciones de las plataformas.

### Por qué las cookies son necesarias

YouTube y YouTube Music han implementado restricciones que requieren autenticación para acceder a ciertos contenidos. Las cookies de una sesión activa de navegador permiten que el bot evada estas restricciones y reproduzca música de ambos servicios.

### Cómo obtener cookies

1. **Inicia sesión en tu cuenta de Google** en tu navegador (Chrome, Edge o Firefox).

2. **Instala la extensión Get cookies.txt:**
   - Chrome/Edge: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid)
   - Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

3. **Ve a YouTube:** Accede a `youtube.com`.

4. **Exporta los cookies:**
   - Haz clic en el **menú de extensiones** de tu navegador.
   - Haz clic en el icono de la extensión **Get cookies.txt LOCALLY**.
   - Haz clic en **"Export All Cookies"**.
   - Haz clic en el botón de **Download**.
   - El navegador puede preguntar dónde guardar el archivo (elige un lugar accesible).
   - De lo contrario, estará en la carpeta **Downloads**.

5. **Sube el archivo** a un directorio accesible en tu servidor (ej: `/root/cookies.txt`).

### Obtención de la ruta del archivo de cookies

Al crear o actualizar bots, el script solicitará la **ruta absoluta** de tu archivo de cookies. Si subiste el archivo a tu servidor, utiliza este comando para obtener la ruta completa:

**Ejemplo: si estás en la carpeta donde subiste el cookies.txt**

```bash
# Navega al directorio que contiene el cookies.txt
cd /ruta/hacia/tu/carpeta

# Obtén la ruta completa
pwd
# Salida: /root/mis-cookies

# O bien obtén la ruta directamente del archivo
realpath cookies.txt
# Salida: /root/mis-cookies/cookies.txt
```

**Comando rápido para obtener la ruta:**
```bash
echo "$(pwd)/cookies.txt"
# Salida: /root/mis-cookies/cookies.txt
```

Copia esta ruta completa y pégala cuando el script de creación o actualización del bot la solicite.

> [!IMPORTANT]
> **Nota:** No utilices archivos de cookies muy grandes. Si el archivo de cookies es demasiado grande, yt-dlp podría no reconocerlo y el bot no reproducirá música. Usa cookies únicamente de los dominios de YouTube/Google.

### Actualización de cookies expiradas

Los cookies expiran periódicamente. Cuando la reproducción de YouTube deje de funcionar:

1. **Genera nuevas cookies** siguiendo los pasos de arriba.
2. **Actualiza todos los bots** con el script de Docker:
   - Ejecuta `./ttbotdocker.sh`.
   - Selecciona la opción `2` (Manage Bots).
   - Selecciona la opción `7` (Update Cookies - All Bots).
   - Introduce la ruta a tu nuevo archivo de cookies.
   - El script actualizará y reiniciará automáticamente todos los bots.

### Actualización manual de cookies

Alternativamente, actualiza los cookies manualmente:
1. Copia el nuevo `cookies.txt` en cada carpeta del bot en `bots/[nombre_bot]/`.
2. Reinicia los bots afectados.

---

## 🌍 Idiomas Soportados

TTMediaBot soporta múltiples idiomas. Cambia el idioma usando el comando de administrador `cl`.

**Idiomas disponibles:**
- `ar` - Árabe
- `en` - Inglés
- `es` - Español
- `hu` - Húngaro
- `id` - Indonesio
- `pt_BR` - Portugués de Brasil
- `ru` - Ruso
- `tr` - Turco

**Ejemplo:** Envía `cl pt_BR` para cambiar el idioma a Portugués de Brasil.

---

## 🔧 Solución de Problemas

### El bot no reproduce música de YouTube

**Sintomas:** El bot se conecta pero no reproduce pistas de YouTube.

**Soluciones:**
1. **Verifica los cookies:**
   - Los cookies pueden haber expirado.
   - Genera nuevas cookies y actualiza (ver la sección Cookies).
   - Verifica la ruta del archivo de cookies en el `config.json`.

2. **Verifica que el archivo de cookies existe:**
   ```bash
   ls -la bots/[nombre_bot]/cookies.txt
   ```

3. **Verifica los logs del bot:**
   - **Logs de Docker:**
     ```bash
     docker logs [nombre_bot]
     ```
   - **Archivo de log:** Verifica `bots/[nombre_bot]/TTMediaBot.log` directamente.

### El bot no se conecta al servidor

**Sintomas:** El bot no aparece en línea.

**Soluciones:**
1. **Verifica los datos del servidor:**
   - Comprueba la dirección y los puertos en `config.json`.
   - Prueba la conectividad con el servidor: `ping [direccion_servidor]`.

2. **Verifica las credenciales:**
   - Asegúrate de que el usuario y la contraseña sean correctos.
   - Confirma que la cuenta del bot existe en el servidor TeamTalk.

3. **Verifica el ajuste de cifrado:**
   - Si el servidor utiliza cifrado, establece `"encrypted": true` en la configuración.
   - **Nota:** El bot obtiene y confía en el certificado SSL del servidor dinámicamente si no se proporciona un archivo de certificado local (`ttservercert.pem`).

4. **Mira los logs:**
   - **Docker:** `docker logs [nombre_bot]`
   - **Archivo:** `bots/[nombre_bot]/TTMediaBot.log`

### Problemas de Audio / Sin Sonido

**Sintomas:** El bot se conecta pero no hay salida de audio.

**Soluciones:**
1. **Verifica PulseAudio:**
   - PulseAudio se ejecuta dentro del contenedor.
   - Reinicia el bot: `docker restart [nombre_bot]`.

2. **Verifica el volumen:**
   - Envía el comando `v` para verificar el volumen actual.
   - Ajusta el volumen: `v 50`.

3. **Verifica la configuración del dispositivo de sonido:**
   - Comprueba la sección `sound_devices` en `config.json`.

### El contenedor no se inicia

**Sintomas:** El contenedor de Docker se apaga inmediatamente tras arrancar.

**Soluciones:**
1. **Verifica los logs:**
   - **Docker:** `docker logs [nombre_bot]`
   - **Archivo:** `bots/[nombre_bot]/TTMediaBot.log`

2. **Verifica la configuración:**
   - Asegúrate de que `config.json` sea un JSON válido.
   - Comprueba si hay errores de sintaxis.

3. **Recrea el contenedor:**
   - Elimina y vuelve a crear el bot usando `ttbotdocker.sh`.

### Errores de Permiso

**Sintomas:** El bot no puede leer o escribir archivos.

**Soluciones:**
1. **Corrige los permisos:**
   ```bash
   sudo chown -R 1000:1000 bots/[nombre_bot]
   ```

2. **Ejecuta el script como root:**
   - Usa siempre `sudo ./ttbotdocker.sh`.

---

## ❓ FAQ (Preguntas Frecuentes)

### P: ¿Puedo ejecutar varios bots en el mismo servidor?
**R:** Sí. El bot soporta múltiples instancias. Usa la función de creación por lote en `ttbotdocker.sh` o créalos uno a uno. Cada bot tendrá su propio contenedor y configuración.

### P: ¿Cómo añado más administradores?
**R:** De dos formas:
- **Mediante comando:** Envía `ua +nombre_usuario` al bot (requiere privilegios previos de administrador).
- **Mediante configuración:** Edita `bots/[nombre_bot]/config.json`, añade el nombre de usuario al arreglo `teamtalk.users.admins` y reinicia.

### P: ¿Cómo realizo una copia de seguridad de mis configuraciones?
**R:** Copia todo el directorio `bots`:
```bash
cp -r bots bots_respaldo_$(date +%Y%m%d)
```

### P: ¿Puedo usar las mismas cookies para todos los bots?
**R:** Sí. Usa la opción "Update Cookies (All Bots)" en el menú de gestión para aplicar el mismo archivo de cookies a todos a la vez.

### P: El bot se desconecta continuamente. ¿Qué hago?
**R:** Comprueba:
- La estabilidad de la red.
- El estado del servidor.
- Los logs del bot: `docker logs [nombre_bot]` o `bots/[nombre_bot]/TTMediaBot.log`.
- Aumenta el valor de `reconnection_timeout` en `config.json`.

### P: ¿Cómo cambio el apodo del bot?
**R:** De dos formas:
- **Mediante comando:** Envía `cn NuevoApodo` (solo administradores).
- **Mediante configuración:** Modifica `teamtalk.nickname` en `config.json` y reinicia.

### P: ¿Puedo conectar bots a diferentes servidores TeamTalk?
**R:** ¡Por supuesto! Cada contenedor de bot puede conectarse a un servidor diferente. Solo especifica las direcciones correspondientes en la creación o configuración.

### P: ¿Cuántos recursos consume cada bot?
**R:** Aproximadamente por contenedor:
- **RAM:** 100-200 MB (inactivo), 200-400 MB (reproduciendo).
- **CPU:** Mínimo al estar inactivo, moderado al transcodificar.
- **Disco:** ~500 MB por bot (incluidas dependencias).

### P: ¿Qué ocurre si actualizo el código del repositorio?
**R:** Las configuraciones en el directorio `bots` se mantendrán intactas. Tras actualizar el repositorio:
1. Reconstruye la imagen Docker: `docker build -t ttmediabot .`
2. Recrea los contenedores usando la opción correspondiente en el script.

---

## 📊 Logs y Monitoreo

### Visualización de Logs en Tiempo Real

**Para un bot en particular:**
```bash
docker logs -f [nombre_bot]
```

**Para todos los bots:**
```bash
docker logs -f $(docker ps -q -f "label=role=ttmediabot")
```

### Ubicación de los Archivos de Log

Cada bot almacena logs en su directorio:
```
bots/[nombre_bot]/TTMediaBot.log
```

### Configuración del Log

Edita los parámetros en `config.json`:

```json
"logger": {
    "log": true,
    "level": "INFO",
    "format": "%(levelname)s [%(asctime)s]: %(message)s",
    "mode": "FILE",
    "file_name": "TTMediaBot.log",
    "max_file_size": 0,
    "backup_count": 0
}
```

**Niveles de log:**
- `DEBUG`: Información detallada para diagnóstico.
- `INFO`: Mensajes informativos generales (por defecto).
- `WARNING`: Mensajes de advertencia.
- `ERROR`: Solo mensajes de error.

**Activar log de depuración (debug):**
Cambia `"level": "INFO"` por `"level": "DEBUG"` y reinicia el bot.

### Monitoreo del Estado de los Bots

**Ver contenedores activos:**
```bash
docker ps -f "label=role=ttmediabot"
```

**Ver todos los contenedores (incluyendo detenidos):**
```bash
docker ps -a -f "label=role=ttmediabot"
```

**Ver estadísticas de recursos:**
```bash
docker stats $(docker ps -q -f "label=role=ttmediabot")
```
