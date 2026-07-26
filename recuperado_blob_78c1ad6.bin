# TTMediaBot

**¡Hola! Soy João Almeida.** Bienvenido a mi bifurcación **TTMediaBot**, un completo robot de transmisión de medios para TeamTalk 5. Este repositorio se centra en ofrecer mejoras constantes, estabilidad y nuevas funciones, como soporte exclusivo para YouTube Music.

> 🔗 **Mi repositorio:** [https://github.com/JoaoDEVWHADS/TTMediaBot](https://github.com/JoaoDEVWHADS/TTMediaBot)

---

> **Nota:** Este repositorio es una bifurcación de [TTMediaBot original](https://github.com/gumerov-amir/TTMediaBot).

Un bot de transmisión de medios rico en funciones para TeamTalk 5, capaz de reproducir música desde varios servicios (YouTube, YouTube Music, archivos locales, URL) con funciones de control avanzadas.


## 📋 Cambios respecto al original

Esta bifurcación incluye varias modificaciones y optimizaciones:

- **Servicios eliminados:** Se eliminó la integración de Yandex Music y VK
- **Actualización de TeamTalk SDK:** Actualizado a TeamTalk SDK 5.8.1 para mejorar el rendimiento
- **Soporte de arquitectura ARM64:** Se agregó soporte nativo para la arquitectura ARM64 (como servidores Raspberry Pi y AWS Graviton) con detección automática de plataforma y descargas de biblioteca durante la instalación.
  > [!NOTE]

> En los sistemas `x86_64`, la instalación permanece intacta y es mínima. En los sistemas `ARM`, el instalador y Dockerfile instalan condicionalmente dependencias adicionales (como `libportaudio2`) requeridas por la versión ARM del SDK de TeamTalk para ejecutarse.
- **Compatibilidad con distribución universal de Linux:** El instalador (`ttbotdocker.sh` / `install_git_clone.sh`) ahora admite dinámicamente la configuración automática de Docker y las dependencias en cualquier distribución principal (Ubuntu, Debian, CentOS, RHEL, Fedora, Rocky Linux, AlmaLinux, Raspbian, Arch, etc.) utilizando el instalador universal oficial y las alternativas del administrador de paquetes dinámicos para `jq`.
- **Docker Containerization:** El bot se ejecuta en contenedores Docker basados ​​en Debian 11 y Python 3.10, lo que garantiza la compatibilidad con dependencias heredadas y al mismo tiempo mantiene la estabilidad.
- **Estabilidad comprobada:** Desde que encontré este bot por primera vez en 2021, las adaptaciones realizadas para evitar las restricciones de YouTube, combinadas con las optimizaciones de 2021/2022, han demostrado ser excelentes y confiables.

## 🆕 Últimas actualizaciones

Para ver el historial completo de actualizaciones, incluidas todas las funciones nuevas, correcciones de errores y optimizaciones, consulte el registro de cambios.

> 📋 **[Ver registro de cambios completo →](CHANGELOG.md)**


## 🎵 Soporte de música de YouTube

Esta bifurcación incluye soporte optimizado para **YouTube Music** junto con YouTube normal:


- **Integración de la API de búsqueda de YouTube:** Utiliza la API de búsqueda de YouTube para un descubrimiento de música rápido y confiable.
- **Bibliotecas optimizadas:**
  - YouTube utiliza `py-yt-search`, una biblioteca Python rápida y moderna para búsquedas en YouTube
  - YouTube Music utiliza `ytmusicapi`, la biblioteca API oficial de YouTube Music
  - Ambos servicios utilizan `yt-dlp` para la extracción de audio.
- **Enfoque en el rendimiento:** Diseñado para ejecutarse con cuellos de botella mínimos, lo que garantiza una reproducción fluida y resultados de búsqueda rápidos.
- **Sistema de cookies unificado:** Tanto YouTube como YouTube Music utilizan la misma configuración de cookies para la autenticación.
- **📦 Descargas de listas de reproducción y álbumes:** Soporte completo para descargar colecciones enteras mediante el comando `dlp` con nombres que tienen en cuenta los metadatos
- **🕵️ Progreso de PM en tiempo real:** Manténgase actualizado sobre sus descargas sin saturar el canal

Cambie entre servicios usando el comando `sv`:
- `sv yt` - Cambiar a YouTube
- `sv ytm` - Cambiar a YouTube Music

> [!NOTE]

> **Función exclusiva:** La compatibilidad con YouTube Music es exclusiva de esta bifurcación y no está disponible en el proyecto TTMediaBot original.

## 🔗 Descarga basada en enlaces y almacenamiento local

Esta bifurcación incluye un sistema avanzado de descarga basado en enlaces que permite a los usuarios poner en cola enlaces de medios, enumerarlos, administrarlos y descargarlos secuencialmente o en archivos comprimidos.

### Comandos
- **`aad [enlace]`**: Agrega un único enlace a su lista.
- **`ad [enlace1] [enlace2] ...`**: Agrega múltiples enlaces separados por espacios a su lista.
- **`ld`**: enumera todos los enlaces actualmente en su lista.
- **`tercer [número/enlace]`**: Elimina un enlace de su lista por índice o URL.
- **`ldd [enlace]`**: Descarga un enlace directamente y lo sube al canal.
- **`ads`**: Descarga tu lista. Le solicita que seleccione:
  - **Opción 1 (Normal):** Descarga cada pista individualmente y la sube al canal.
  - **Opción 2 (ZIP):** Resuelve y comprime todas las pistas en un único archivo ZIP y luego lo sube al canal.
- **`adsc`**: alterna el **modo de descarga local** (volátil). Cuando está habilitado:
  - Las pistas de la lista de "anuncios" se almacenan directamente en el sistema de archivos VPS en lugar de cargarse en TeamTalk.
  - La opción 1 almacena archivos en `data/Downloads/music/` (host: `bots/nomedobot/Downloads/music/`).
  - La opción 2 almacena archivos ZIP en `data/Downloads/zips/` (host: `bots/nomedobot/Downloads/zips/`).
  - Los archivos guardados localmente nunca se eliminan automáticamente.
  - Muestra un informe final de éxito/error al finalizar.

## 🚀 Fácil instalación (recomendado)

Este script instalará Git automáticamente (si es necesario), clonará el repositorio y configurará el entorno Docker.

1. **Descargue y ejecute el instalador:**
    ```bash
    wget https://raw.githubusercontent.com/JoaoDEVWHADS/TTMediaBot/master/install_git_clone.sh
    sudo chmod +x install_git_clone.sh
    sudo ./install_git_clone.sh
    ```

2. **Monitorear la terminal:**
    *   El script instalará automáticamente todas las dependencias (incluido Docker si es necesario).
    *   Esté atento a la salida del terminal para seguir el progreso de la instalación.
    *   Puede administrar varios bots, actualizar código y cambiar configuraciones a través del administrador de Docker.

---

## ⚙️ Configuración manual

Si necesita editar manualmente las configuraciones del bot después de la instalación:

1. **Los archivos de configuración** se encuentran en el directorio `bots` dentro de la carpeta `TTMediaBot` después de la configuración inicial.
2. **Haga sus cambios** en los archivos de configuración según sea necesario
3. **Reinicie el bot** usando uno de estos métodos:
   - **A través del script Docker:** Ejecute `./ttbotdocker.sh`, seleccione la opción `2` (Administrar Bots), luego elija la opción de reinicio (generalmente la opción `2`)
   - **A través del comando del bot:** Enviar `rs` como mensaje privado al bot (requiere privilegios de administrador)

---

## 🎮 Comandos

Envía estos comandos al bot mediante mensaje privado (PM) o en el canal (si está habilitado).

### Comandos de usuario
| Dominio | Argumentos | Descripción |
| :--- | :--- | :--- |
| **h** || Muestra ayuda de comando. |
| **pag** | `[consulta]` | Reproduce pistas encontradas para consulta. Si no hay ninguna consulta, se detiene/reanuda. |
| **tú** | `[URL]` | Reproduce una secuencia/archivo desde una URL directa. |
| **s** || Detiene la reproducción. |
| **norte** || Reproduce la siguiente pista. |
| **b** || Reproduce la pista anterior. |
| **v** | `[0-100]` | Establece el volumen. Ningún argumento muestra el volumen actual. |
| **algo** | `[segundos]` | Busca hacia atrás. Paso predeterminado si no hay argumento. |
| **sf** | `[segundos]` | Busca adelante. Paso predeterminado si no hay argumento. |
| **do** | `[número]` | Selecciona una pista por número de los resultados de búsqueda. |
| **metro** | `[modo]` | Establece el modo de reproducción: `SingleTrack`, `RepeatTrack`, `TrackList`, `RepeatTrackList`, `Random`. |
| **sp** | `[0,25-4]` | Establece la velocidad de reproducción. |
| **sv** | `[servicio]` | Cambia el servicio (por ejemplo, `sv yt`, `sv ytm`). |
| **F** | `[+/-][núm]` | Gestión de favoritos. Listas `f`. `f +` agrega corriente. `f -` elimina. Se reproduce `f [núm]`. |
| **gl** || Obtiene un enlace directo a la pista actual. |
| **dl** || Descarga la pista actual y la sube al canal. |
| **dlv** || Descarga la pista actual como video y la sube al canal. |
| **dlp** | `[URL]` | Descarga todas las pistas de una lista de reproducción/URL de álbum, las comprime y las sube al canal. |
| **ad** | `[enlace]` | Agrega un único enlace/URL a su lista de descargas personalizada. |
| **anuncio** | `[enlaces]` | Agrega múltiples enlaces separados por espacios a la lista de descargas. |
| **viejo** || Enumera todos los enlaces actualmente en la lista de descargas. |
| **tercer** | `[número/enlace]` | Elimina un enlace de la lista de descargas por su índice o URL. |
| **ldd** | `[enlace]` | Descarga un enlace directamente y lo sube al canal TeamTalk. |
| **anuncios** | `[1/2]` | Lista de descargas: Opción 1 (Normal secuencialmente) u Opción 2 (comprimido ZIP). |
| **adsc** || Alterna el modo de descarga local: guarda archivos localmente en el VPS en lugar de cargarlos. |
| **r** | `[número]` | Reproducciones de recientes. `r` enumera los recientes. |
| **jc** || Hace que el bot se una a tu canal actual. |
| **qa** | `[consulta]` | Agrega una pista a la cola. |
| **ql** || Enumera todas las pistas actualmente en la cola. |
| **qr** | `[número]` | Elimina una pista específica de la cola. |
| **control de calidad** || Borra toda la cola. |
| **preguntas** || Salta la pista actual y reproduce la siguiente de la cola. |
| **sr** | `[activar/desactivar]` | Alterna el modo de resultados de búsqueda. Cuando está activo, `p QUERY` muestra una lista numerada en lugar de reproducirse inmediatamente. Guardar con `sc`. |
| **sl** | `[número]` | Selecciona y reproduce el resultado NÚMERO de la última lista de búsqueda `sr`. |
| **slc** | `[número]` | Establece cuántos resultados se muestran en el modo `sr` (predeterminado 5). Ningún argumento muestra el recuento actual. |
| **a** || Muestra sobre información. |

### Comandos de administrador
*Requiere privilegios de administrador definidos en `config.json`.*

| Dominio | Argumentos | Descripción |
| :--- | :--- | :--- |
| **cg** | `[n/m/f]` | Cambia el género del bot. |
| **cl** | `[código]` | Cambia el idioma (por ejemplo, `en`, `ru`, `pt_BR`). |
| **cn** | `[nombre]` | Cambia el apodo del bot. |
| **cs** | `[texto]` | Cambia el texto del estado del bot. |
| **cc** | `[r/f]` | Borra el caché (`r`=recientes, `f`=favoritos). |
| **centímetro** || Alterna el envío de mensajes del canal. |
| **ajc** | `[id] [contraseña]` | Forzar la entrada al canal por ID. |
| **antes de Cristo** | `[+/-cmd]` | Bloquea/Desbloquea un comando. |
| **l** || Bloquea/desbloquea el bot (solo los administradores pueden usarlo). |
| **ua** | `[+/-usuario]` | Agrega o elimina usuarios administradores. |
| **ub** | `[+/-usuario]` | Agrega/elimina usuarios prohibidos. |
| **eh** || Alterna el manejo de eventos internos. |
| **Carolina del Sur** || Guarda la configuración actual en un archivo. |
| **Virginia** || Alterna la transmisión de voz. |
| **rs** || Reinicia el bot. |
| **q** || Sale del robot. |
| **gcid** || Obtiene el ID del canal actual. |

---

## 🐳 Script de administración de Docker (`ttbotdocker.sh`)

El script `ttbotdocker.sh` es una herramienta de gestión integral para TTMediaBot. Proporciona una interfaz basada en menús para manejar todos los aspectos de la implementación y administración de bots.

### Opciones del menú principal

#### 1. Crear robot
Crea una nueva instancia de bot con un asistente de configuración completo:
- **Nombre del bot:** Nombre del contenedor y de la carpeta
- **Configuración del servidor:** Nombre de host, puertos TCP/UDP, cifrado
- **Credenciales:** Nombre de usuario y contraseña
- **Cookies:** Ruta al archivo de cookies de YouTube
- **Creación por lotes:** Crea varios bots a la vez con numeración automática
  - Detecta automáticamente los números de bot existentes y continúa la secuencia
  - Nomenclatura separada para contenedores y apodos
  - Previene conflictos en el mismo servidor TeamTalk

#### 2. Administrar robots
Submenú de gestión integral de bots con 12 opciones:

**2.1. Iniciar todos los bots**
- Inicia todos los contenedores de bots detenidos
- Utiliza el filtrado de etiquetas de Docker (`role=ttmediabot`)

**2.2. Reiniciar todos los bots**
- Detiene todos los bots (tiempo de espera de 1 segundo)
- Inmediatamente los inicia nuevamente
- Útil para aplicar cambios de configuración

**2.3. Detener todos los robots**
- Detiene con gracia todos los bots en ejecución
- Tiempo de espera de 1 segundo para un apagado limpio

**2.4. Eliminar bot**
- Menú interactivo para seleccionar y eliminar un solo bot
- Muestra una lista numerada de todos los bots.
- Elimina tanto el contenedor como la carpeta de configuración.
- Requiere confirmación antes de la eliminación

**2.5. Eliminación masiva de bots**
- Eliminar varios bots en una sola operación
- Ingrese números separados por espacios (por ejemplo, `1 3 5`)
- Utilice la opción `0` para **eliminar TODOS los bots** simultáneamente
- Muestra un resumen antes de la eliminación
- Eliminación eficiente de contenedores en paralelo

**2.6. Bot duplicado**
- Clonar la configuración de un bot existente
- Seleccione el bot de origen de la lista numerada
- Muestra la dirección del servidor para cada bot.
- Soporte de duplicación por lotes (cree múltiples copias)
- Numeración automática para contenedores y solicita explícitamente **NICKNAME BASE**
- Detección inteligente de conflictos: evita la clonación si el nombre base elegido ya existe

**2.7. Actualizar cookies (todos los bots)**
- Actualiza las cookies de YouTube para todos los bots a la vez
- Copia el nuevo archivo de cookies a todos los directorios del bot.
- Reinicia automáticamente todos los bots para aplicar cambios.
- Establece permisos de archivos correctos (1000:1000)

**2.8. Reiniciar con temporizador**
- Detiene todos los bots, espera el tiempo especificado y luego los inicia
- Útil para el mantenimiento coordinado del servidor
- Temporizador visual de cuenta regresiva
- Tiempo especificado en segundos

**2.9. Configuración de actualización masiva**
- Actualizar la configuración para todos los bots simultáneamente
- Elija qué actualizar:
1. Servidor (nombre de host)
2. Puertos (TCP/UDP)
3. Cifrado
4. Credenciales (nombre de usuario/contraseña)
5. Todo
- Muestra la configuración actual del primer bot.
- Vista previa de los cambios antes de aplicar
- Actualiza todos los archivos del bot `config.json`

> [!WARNING]

> **Importante:** Esta función está diseñada para bots en el **mismo servidor**. Si tiene bots conectados a varios servidores TeamTalk diferentes, deberá actualizarlos manualmente. El uso de esta función configurará todos los bots con la misma configuración de servidor.

**2.10. Bots de copia de seguridad/restauración**
- Utilidad portátil de copia de seguridad/restauración para configuración y caché de bots.
- Guarda las copias de seguridad comprimidas (`.tar.gz`) en un directorio `backups/`.
- La restauración vuelve a implementar dinámicamente las configuraciones del bot y recrea los contenedores Docker.

**2.11. Borrar todos los registros de bots**
- Utilidad de borrado rápido que elimina todos los archivos `*.log` de todas las carpetas de datos del bot para liberar espacio en el disco.

**2.12. Volver al menú principal**

#### 3. Reconstruir imagen/actualizar código
Actualiza el código del bot y reconstruye la imagen de Docker:
- Reconstruye la imagen de Docker con `CACHEBUST` para garantizar un código nuevo
- Recrea contenedores con nueva imagen.
- Reinicia solo los bots que se ejecutan anteriormente

#### 4. Desinstalar todo
Limpieza completa de la instalación de TTMediaBot:
- Detiene todos los contenedores de bots
- Elimina todos los contenedores
- Elimina todas las carpetas del bot.
- Elimina la imagen de Docker
- **Advertencia:** ¡Esto es irreversible!

#### 5. Busque actualizaciones
Comprueba automáticamente el repositorio de GitHub en busca de actualizaciones.
- Utiliza `update.sh` para comparar el código local con el repositorio remoto
- Realiza copias de seguridad de la configuración de forma segura antes de actualizar
- Incluye una pausa al final para que los usuarios puedan leer la consola.

#### 6. Activar/desactivar actualizaciones automáticas
Menú dedicado para alternar actualizaciones en segundo plano mediante el enmascaramiento systemd.

#### 7. Limpiar caché de Docker (sin usar)
Herramienta de limpieza avanzada para recuperar espacio en disco sin afectar a los bots en ejecución:
- **Docker Prune:** Elimina contenedores detenidos e imágenes no utilizadas.
- **Limpieza de Buildx:** Limpia los cachés de compilación persistentes.
- **Registros del sistema:** Aspira registros `journalctl` de más de 1 día.
- **Huella cero:** Garantiza que el sistema host se mantenga eficiente.

#### 8. Salir
Cierra el guión

### Funciones automáticas

El guión automáticamente:
- **Comprueba si hay actualizaciones** automáticamente al iniciar si `update.sh` está presente
- **Instala dependencias** (Docker, jq) en la primera ejecución
- **Crea una imagen de Docker** automáticamente y obliga a PIP a actualizar las bibliotecas (`-U`) en cada reconstrucción
- **Sin mensajes de inicio:** La reconstrucción ahora es una opción de menú manual (Opción 3), lo que hace que el inicio sea más rápido
- **Crea la estructura del directorio `bots`**
- **Detecta conflictos** (nombres de contenedores, apodos en el mismo servidor)
- **Establece permisos** correctamente para volúmenes Docker
- **Utiliza etiquetas** para filtrar fácilmente los contenedores

---

## 🔄 Script de actualización independiente (`update.sh`)

Si ya tiene bots instalados y solo desea actualizar el código sin usar el administrador Docker completo, puede usar el script independiente `update.sh`.

**Cómo utilizar:**
1. Descargue el script a su carpeta `TTMediaBot`:
   ```bash
   wget https://raw.githubusercontent.com/JoaoDEVWHADS/TTMediaBot/master/update.sh
   chmod +x update.sh
   ```
2. Ejecútelo:
   ```bash
   sudo ./update.sh
   ```

Este script actualizará el repositorio, reconstruirá la imagen y recreará los contenedores, asegurando que todo esté actualizado.

---

## 🍪 Configuración de cookies de YouTube y YouTube Music

Las cookies son **esenciales** para que el bot reproduzca música tanto de **YouTube** como de **YouTube Music** debido a restricciones de la plataforma.

### Por qué se necesitan las cookies

YouTube y YouTube Music han implementado restricciones que requieren autenticación para acceder a determinado contenido. Las cookies de una sesión de navegador autenticada permiten que el bot evite estas restricciones y reproduzca música desde ambos servicios.

### Cómo obtener cookies

1. **Inicie sesión en su cuenta de Google** en su navegador (Chrome, Edge o Firefox)

2. **Instale la extensión Obtener cookies.txt:**
   - Cromo/Borde: [Obtener cookies.txt LOCALMENTE](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid)
   - Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

3. **Navega a YouTube:** Ve a `youtube.com`

4. **Exportar cookies:**
   - Haga clic en el **menú Extensiones** en su navegador
   - Haga clic en el ícono de extensión **Obtener cookies.txt LOCALMENTE**
   - Haga clic en **"Exportar todas las cookies"**
   - Haga clic en el **botón Descargar**
   - Es posible que su navegador le pregunte dónde guardar el archivo; elija una ubicación a la que pueda acceder
   - Si no se le solicita, el archivo estará en su carpeta **Descargas**

5. **Coloque el archivo** en una ubicación accesible en su servidor (por ejemplo, `/root/cookies.txt`)

### Obtener la ruta del archivo de cookies

Al crear o actualizar bots, el script le pedirá la **ruta completa** a su archivo de cookies. Si cargó el archivo en su servidor, use este comando para obtener la ruta absoluta:

**Ejemplo: si estás en el directorio donde subiste cookies.txt**

```bash
# Navigate to the directory containing cookies.txt
cd /path/to/your/directory

# Get the full path
pwd
# Output: /root/my-cookies

# Or get the full path directly
realpath cookies.txt
# Output: /root/my-cookies/cookies.txt
```

**Comando rápido para obtener la ruta:**
```bash
echo "$(pwd)/cookies.txt"
# Output: /root/my-cookies/cookies.txt
```

Copie esta ruta completa y péguela cuando el script de creación o actualización del bot solicite la ubicación del archivo de cookies.

> [!IMPORTANT]

> **Nota:** No utilice archivos de cookies muy grandes. Si el archivo de cookies es demasiado grande, es posible que yt-dlp no lo reconozca y el bot no reproduzca música. Utilice cookies únicamente de dominios de YouTube/Google.

### Actualización de cookies caducadas

Las cookies caducan periódicamente. Cuando la reproducción de YouTube deja de funcionar:

1. **Generar nuevas cookies** siguiendo los pasos anteriores
2. **Actualice todos los bots** usando el script Docker:
   - Ejecute `./ttbotdocker.sh`
   - Seleccione la opción `2` (Administrar Bots)
   - Seleccione la opción `7` (Actualizar Cookies - Todos los Bots)
   - Ingrese la ruta a su nuevo archivo de cookies
   - El script actualizará y reiniciará automáticamente todos los bots.

### Actualización manual de cookies

Alternativamente, actualice las cookies manualmente:
1. Copie el nuevo `cookies.txt` a cada carpeta de bot en `bots/[bot_name]/`
2. Reinicie los bots afectados

---

## 🌍 Idiomas admitidos

TTMediaBot admite varios idiomas. Cambie el idioma usando el comando de administración `cl`.

**Idiomas disponibles:**
- `ar` - árabe
- `en` - inglés
- `es` - español
- `hu` - húngaro
- `id` - indonesio
- `pt_BR` - portugués brasileño
- `ru` - ruso
- `tr` - turco

**Ejemplo:** Envíe `cl pt_BR` para cambiar al portugués brasileño.

---

## 🔧 Solución de problemas

### El robot no reproduce música de YouTube

**Síntomas:** El bot se conecta pero no reproduce pistas de YouTube

**Soluciones:**
1. **Comprueba las cookies:**
   - Es posible que las cookies hayan caducado
   - Generar nuevas cookies y actualizar (ver apartado Cookies de YouTube)
   - Verifique la ruta del archivo de cookies en `config.json`

2. **Verifique que el archivo de cookies exista:**
   ```bash
   ls -la bots/[bot_name]/cookies.txt
   ```

3. **Verifique los registros del bot:**
   - **Registros de Docker:**
     ```bash
     docker logs [bot_name]
     ```
   - **Archivo de registro:** Verifique `bots/[bot_name]/TTMediaBot.log` directamente.

### El bot no se conecta al servidor

**Síntomas:** El bot no aparece en línea

**Soluciones:**
1. **Verificar los detalles del servidor:**
   - Verifique el nombre de host y los puertos en `config.json`
   - Probar la conectividad del servidor: `ping [nombre de host]`

2. **Verificar credenciales:**
   - Verifique que el nombre de usuario y la contraseña sean correctos
   - Asegúrese de que la cuenta del bot exista en el servidor TeamTalk

3. **Compruebe la configuración de cifrado:**
   - Si el servidor usa cifrado, configure `"cifrado": verdadero` en la configuración.
   - **Nota:** El bot busca automáticamente y confía en el certificado SSL del servidor de forma dinámica (similar al cliente de Windows) si no se proporciona ningún certificado de CA local (`ttservercert.pem`).

4. **Ver registros:**
   - **Docker:** `registros de Docker [nombre_bot]`
   - **Archivo:** `bots/[nombre_bot]/TTMediaBot.log`

### Problemas de audio/Sin sonido

**Síntomas:** El bot se conecta pero no hay salida de audio

**Soluciones:**
1. **Comprueba PulseAudio:**
   - PulseAudio se ejecuta dentro del contenedor
   - Reinicie el bot: `docker restart [bot_name]`

2. **Verificar volumen:**
   - Envíe el comando `v` para verificar el volumen actual
   - Establecer volumen: `v 50`

3. **Verifique la configuración del dispositivo de audio:**
   - Consulte la sección `sound_devices` en `config.json`

### El contenedor no arranca

**Síntomas:** El contenedor Docker sale inmediatamente

**Soluciones:**
1. **Verificar registros:**
   - **Docker:** `registros de Docker [nombre_bot]`
   - **Archivo:** `bots/[nombre_bot]/TTMediaBot.log`

2. **Verificar configuración:**
   - Asegúrese de que `config.json` sea JSON válido
   - Comprobar errores de sintaxis

3. **Recrear contenedor:**
   - Elimina y recrea el bot usando `ttbotdocker.sh`

### Errores de permiso

**Síntomas:** El robot no puede leer ni escribir archivos.

**Soluciones:**
1. **Reparar permisos:**
   ```bash
   sudo chown -R 1000:1000 bots/[bot_name]
   ```

2. **Ejecutar script como root:**
   - Utilice siempre `sudo ./ttbotdocker.sh`

---

## ❓ Preguntas frecuentes (Preguntas frecuentes)

### P: ¿Puedo ejecutar varios bots en el mismo servidor?
**R:** ¡Sí! El bot admite múltiples instancias. Utilice la función de creación por lotes en `ttbotdocker.sh` o cree bots individualmente. Cada bot tiene su propio contenedor y configuración.

### P: ¿Cómo agrego más administradores?
**R:** Dos maneras:
- **A través del comando:** Envíe `ua +nombre de usuario` al bot (requiere privilegios de administrador existentes)
- **A través de configuración:** Edite `bots/[bot_name]/config.json`, agregue el nombre de usuario a la matriz `teamtalk.users.admins` y luego reinicie

### P: ¿Cómo hago una copia de seguridad de las configuraciones de mi bot?
**R:** Simplemente copie todo el directorio `bots`:
```bash
cp -r bots bots_backup_$(date +%Y%m%d)
```

### P: ¿Puedo utilizar las mismas cookies para todos los bots?
**R:** ¡Sí! Utilice la función "Actualizar cookies (todos los bots)" en el menú de administración para aplicar el mismo archivo de cookies a todos los bots a la vez.

### P: El bot sigue desconectándose. ¿Qué tengo que hacer?
**R:** Verificar:
- Estabilidad de la red
- Estado del servidor
- Registros de bot: `docker logs [bot_name]` o marque `bots/[bot_name]/TTMediaBot.log`
- Aumentar `reconnection_timeout` en `config.json`

### P: ¿Cómo cambio el apodo del bot?
**R:** Dos maneras:
- **A través del comando:** Enviar `cn NewNickname` (solo administrador)
- **A través de configuración:** Edite `teamtalk.nickname` en `config.json`, luego reinicie

### P: ¿Puedo ejecutar bots en diferentes servidores TeamTalk?
**R:** ¡Absolutamente! Cada bot puede conectarse a un servidor diferente. Simplemente especifique diferentes nombres de host durante la creación o en la configuración.

### P: ¿Cuántos recursos utiliza cada bot?
**R:** Cada contenedor de bot utiliza aproximadamente:
- **RAM:** 100-200 MB (inactivo), 200-400 MB (reproduciendo)
- **CPU:** Mínimo cuando está inactivo, moderado al transcodificar audio
- **Disco:** ~500 MB por bot (incluidas las dependencias)

### P: ¿Qué sucede si actualizo el código del repositorio?
**R:** Las configuraciones de su bot en el directorio `bots` se conservan. Después de obtener actualizaciones:
1. Reconstruya la imagen de Docker: `docker build -t ttmediabot.`
2. Recrea contenedores usando la función de recreación del script.

---

---

## 📊 Registros y seguimiento

### Ver registros en tiempo real

**Para un bot específico:**
```bash
docker logs -f [bot_name]
```

**Para todos los robots:**
```bash
docker logs -f $(docker ps -q -f "label=role=ttmediabot")
```

### Ubicación de los archivos de registro

Cada bot almacena registros en su directorio:
```
bots/[bot_name]/TTMediaBot.log
```

### Configuración de registro

Edite la configuración del registro en `config.json`:

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

**Niveles de registro:**
- `DEBUG`: información detallada para diagnosticar problemas
- `INFO` - Mensajes informativos generales (predeterminado)
- `WARNING` - Mensajes de advertencia
- `ERROR`: solo mensajes de error

**Habilitar registro de depuración:**
Cambie `"level": "INFO"` a `"level": "DEBUG"` y reinicie el bot.

### Monitoreo del estado del robot

**Comprueba los bots en ejecución:**
```bash
docker ps -f "label=role=ttmediabot"
```

**Verifique todos los bots (incluidos los detenidos):**
```bash
docker ps -a -f "label=role=ttmediabot"
```

**Verificar uso de recursos:**
```bash
docker stats $(docker ps -q -f "label=role=ttmediabot")
```
  - Confirmación de prueba final: jueves 14 de mayo a las 12:50:00 UTC de 2026
