# Decisiones del proyecto

## Arquitectura de datos

- `data/raw/`: archivos descargados originales; no se modifican.
- `data/bronze/`: primera capa de ingesta y persistencia.
- `data/silver/`: datos limpios, tipados y validados.
- `data/gold/`: tablas analíticas, métricas y agregados finales.
- `data/gold/reportes/`: entregables y reportes generados desde Gold.

## Ejecución

Cada etapa reside en un módulo independiente dentro de `src/`. El archivo
`main.py` las ejecuta en este orden: Bronze, Silver, Gold y Reportes.

## Tarea 1: Exploración de los archivos

### Nota metodológica sobre el script de exploración
El archivo [scripts/explorar_archivos.py](file:///c:/Users/Usuario/Ejercicio_Ecobici_Bronze_Silver_Gold/scripts/explorar_archivos.py) es una herramienta auxiliar desarrollada fuera de `src/` para respetar estrictamente la estructura del pipeline requerida. No es invocado por [main.py](file:///c:/Users/Usuario/Ejercicio_Ecobici_Bronze_Silver_Gold/main.py) y su único propósito es servir como diagnóstico idempotente, inspección en streaming por bloques (`chunksize=500_000`) y generador de evidencia reproducible en [scripts/salida_exploracion.txt](file:///c:/Users/Usuario/Ejercicio_Ecobici_Bronze_Silver_Gold/scripts/salida_exploracion.txt) y [scripts/salida_exploracion.json](file:///c:/Users/Usuario/Ejercicio_Ecobici_Bronze_Silver_Gold/scripts/salida_exploracion.json).

---

### 1. Tabla comparativa: RECORRIDOS

| Característica / Métrica | 2016 | 2019 | 2024 |
| :--- | :--- | :--- | :--- |
| **Nombre archivo dentro del ZIP** | `recorridos-realizados-2016.csv` | `trips_2019.csv` | `badata_ecobici_recorridos_realizados_2024.csv` |
| **Separador de columnas** | Coma (`,`) | Coma (`,`) | Coma (`,`) |
| **Encoding detectado** | `utf-8` | `utf-8` | `utf-8-sig` (contiene BOM `\xef\xbb\xbf`) |
| **Cantidad de columnas** | 15 columnas | 18 columnas | 17 columnas |
| **Nombres exactos de columnas** | `periodo`, `genero_usuario`, `fecha_origen_recorrido`, `id_estacion_origen`, `nombre_estacion_origen`, `long_estacion_origen`, `lat_estacion_origen`, `domicilio_estacion_origen`, `duracion_recorrido`, `fecha_destino_recorrido`, `id_estacion_destino`, `nombre_estacion_destino`, `long_estacion_destino`, `lat_estacion_destino`, `domicilio_estacion_destino` | `""` (leída como `Unnamed: 0`), `Id_recorrido`, `duracion_recorrido`, `fecha_origen_recorrido`, `id_estacion_origen`, `nombre_estacion_origen`, `direccion_estacion_origen`, `long_estacion_origen`, `lat_estacion_origen`, `fecha_destino_recorrido`, `id_estacion_destino`, `nombre_estacion_destino`, `direccion_estacion_destino`, `long_estacion_destino`, `lat_estacion_destino`, `id_usuario`, `modelo_bicicleta`, `género` | `id_recorrido`, `duracion_recorrido`, `fecha_origen_recorrido`, `id_estacion_origen`, `nombre_estacion_origen`, `direccion_estacion_origen`, `long_estacion_origen`, `lat_estacion_origen`, `fecha_destino_recorrido`, `id_estacion_destino`, `nombre_estacion_destino`, `direccion_estacion_destino`, `long_estacion_destino`, `lat_estacion_destino`, `id_usuario`, `modelo_bicicleta`, `genero` |
| **Formato fecha y hora** | `%Y-%m-%d %H:%M:%S`<br>(ej: `2016-01-01 02:21:41`) | `%Y-%m-%d %H:%M:%S`<br>(ej: `2019-02-27 19:44:42`) | `%Y-%m-%d %H:%M:%S`<br>(ej: `2024-01-23 18:36:00`) |
| **¿Trae duración? Formato y unidad** | Sí. Texto formato timedelta de pandas (`0 days HH:MM:SS.ns`), ej: `0 days 00:16:29.000000000` | Sí. Segundos como texto con separador de miles por coma, ej: `2,814` | Sí. Segundos como valor entero numérico en texto, ej: `568` |
| **¿Trae ID de usuario?** | **No** (no existe columna; solo trae `genero_usuario`) | **Sí** (`id_usuario`). Texto con sufijo `BAEcobici` en el 100% de filas; 0 nulos | **Sí** (`id_usuario`). Texto terminado en `.0` en el 100% de filas; 0 nulos |
| **¿Trae ID de viaje?** | **No** (no existe identificador primario de viaje) | **Sí** (`Id_recorrido`). Texto con sufijo `BAEcobici`; 0 duplicados | **Sí** (`id_recorrido`). Texto con dígitos enteros; 1 duplicado |
| **Cantidad TOTAL de filas** | **596.807** | **6.217.004** | **3.559.284** |

---

### 2. Tabla comparativa: USUARIOS

| Característica / Métrica | 2016 | 2019 | 2024 |
| :--- | :--- | :--- | :--- |
| **Nombre archivo CSV** | `usuarios-ecobici-2016.csv` | `usuarios_ecobici_2019.csv` | `usuarios_ecobici_2024.csv` |
| **Separador de columnas** | Coma (`,`) | Coma (`,`) | Coma (`,`) |
| **Encoding detectado** | `utf-8` | `utf-8` | `utf-8-sig` (contiene BOM `\xef\xbb\xbf`) |
| **Columnas exactas** | `id_usuario`, `genero_usuario`, `edad_usuario`, `fecha_alta`, `hora_alta` | `ID_usuario`, `genero_usuario`, `edad_usuario`, `fecha_alta`, `hora_alta` | `id_usuario`, `genero_usuario`, `edad_usuario`, `fecha_alta`, `hora_alta` |
| **Formato fecha_alta y hora_alta** | `fecha_alta`: `%d-%m-%y` (ej: `01-01-16`)<br>`hora_alta`: `%I:%M:%S %p` (12h AM/PM, ej: `3:45:19 AM`) | `fecha_alta`: `%Y-%m-%d` (ej: `2019-12-31`)<br>`hora_alta`: `%H:%M:%S` (24h, ej: `10:46:10`) | `fecha_alta`: `%Y-%m-%d` (ej: `2024-01-18`)<br>`hora_alta`: `%H:%M:%S` (24h, ej: `09:21:02`) |
| **Valores de género encontrados** | `M`: 21.697<br>`F`: 17.784 | `MALE`: 41.107<br>`FEMALE`: 24.285<br>`OTHER`: 17.351<br>`NaN`: 857 | `MALE`: 88.655<br>`FEMALE`: 79.310<br>`OTHER`: 29.112 |
| **Rango de edades** | Mínimo: 16 \| Máximo: 88<br>(0 nulos) | Mínimo: 0 \| Máximo: 935<br>(765 nulos o no numéricos) | Mínimo: 4 \| Máximo: 2021<br>(0 nulos) |
| **IDs nulos / duplicados** | 0 nulos \| 0 duplicados | 0 nulos \| 0 duplicados | 0 nulos \| 0 duplicados |
| **Cantidad TOTAL de filas** | **39.481** | **83.600** | **197.077** |

---

### 3. Impacto esperado en cuarentena (Reglas de calidad y validación)

Los siguientes conteos corresponden a los registros que violan las condiciones de integridad medidas sobre la totalidad de los datos en el PASO 3b. 

> [!NOTA]
> Los conteos se detallan por regla individual y **pueden superponerse** (un mismo registro puede incumplir simultáneamente dos o más criterios de calidad):

| Criterio de cuarentena / validación | 2016 | 2019 | 2024 | Observaciones y diagnóstico |
| :--- | :---: | :---: | :---: | :--- |
| **Recorridos sin fecha de destino (`fecha_destino_recorrido` nula)** | 93.555 | 0 | 3.379 | Viajes incompletos o bicicletas no devueltas en la ventana de captura. |
| **Recorridos sin estación de destino (`id_estacion_destino` nula)** | 0 | 1.760 | 0 | Viajes con estación de arribo no registrada. |
| **Recorridos con fecha de fin anterior al inicio (destino < origen)** | 0 | 0 | 0 | Ningún viaje presentó inversión temporal cronológica. |
| **Recorridos con duración calculada > 86.400 segundos (> 24 hs)** | 0 | 9.048 | 687 | Viajes de duración excesiva o bicicletas retenidas/olvidadas. |
| **Recorridos con ID de viaje duplicado** | No aplica | 0 | 1 | En 2024 el ID `22425357` aparece 2 veces en el archivo. |
| **Fechas con formato inválido (distinto a `%Y-%m-%d %H:%M:%S`)** | 0 | 0 | 0 | El 100% de las fechas no nulas cumple el estándar ISO. |
| **Usuarios con género nulo** | 0 | 857 | 0 | Registrados exclusivamente en el dataset de usuarios 2019. |
| **Usuarios con edad nula o no numérica** | 0 | 765 | 0 | Valores faltantes en usuarios 2019. |
| **Usuarios con edades inverosímiles (< 12 o > 100 años)** | 0 | Presentes | Presentes | 2019 presenta registros de 0 y 935 años. 2024 presenta registros de 4 años y registros donde se ingresó el año de nacimiento como edad (ej. 2021). |

---

### 4. Diferencias detectadas entre años

#### A. Hechos medidos (Evidencia técnica verificada)
1. **Recorridos 2016 sin identificador de viaje ni de usuario**:
   - 2016 no contiene `id_recorrido` ni `id_usuario`. Solo incluye `genero_usuario`. Esto imposibilita el cruce por clave foránea entre los viajes de 2016 y la tabla de usuarios de 2016.
2. **Sufijo `BAEcobici` en IDs de 2019**:
   - En `trips_2019.csv`, el 100% de los `id_usuario` (`6.217.004` filas) y los `Id_recorrido` poseen el sufijo alfanumérico `'BAEcobici'` (ej: `'6243BAEcobici'`).
   - En la tabla de usuarios 2019, la columna se llama `ID_usuario` y los valores son puramente numéricos (ej: `'627966'`).
3. **Serialización flotante `".0"` en `id_usuario` 2024**:
   - En recorridos 2024, el 100% de las filas (`3.559.284`) contiene `id_usuario` terminado en `".0"` (ej: `'992557.0'`), sin ningún valor nulo. En cambio, en la tabla de usuarios 2024 son enteros limpios (ej: `'1094487'`).
4. **Columna sin nombre en recorridos 2019**:
   - La primera columna viene con cabecera vacía `""` (que pandas interpreta como `Unnamed: 0`), originada por haber guardado el DataFrame original con su índice numérico secuencial.
5. **Duración en tres formatos heterogéneos**:
   - 2016: string representativo de timedelta de pandas (`0 days 00:16:29.000000000`).
   - 2019: segundos como texto con comas de miles (`2,814`).
   - 2024: segundos como texto entero estándar (`568`), conteniendo además viajes con duración `0`.
6. **Desacople y variación en fechas de alta de usuarios**:
   - 2016 registra `fecha_alta` en formato `%d-%m-%y` y `hora_alta` en formato de 12 horas con indicador AM/PM (`%I:%M:%S %p`).
   - 2019 y 2024 registran `fecha_alta` en formato `%Y-%m-%d` y `hora_alta` en formato de 24 horas (`%H:%M:%S`).
7. **Discrepancia en taxonomía de género**:
   - 2016 utiliza `M` y `F` tanto en usuarios como en recorridos.
   - 2019 y 2024 utilizan `MALE`, `FEMALE` y `OTHER`, presentando 2019 además 857 valores nulos.
   - El nombre de la columna en recorridos varía: `genero_usuario` en 2016, `género` (con tilde) en 2019 y `genero` (sin tilde) en 2024.
8. **Edades inverosímiles en usuarios**:
   - 2016 presenta un rango biológicamente plausible (16 a 88 años).
   - 2019 tiene un rango de 0 a 935 años, con 765 nulos.
   - 2024 tiene un rango de 4 a 2021 años (usuarios que cargaron su año de nacimiento en el casillero de edad).
9. **Marca BOM en 2024**:
   - Los archivos de 2024 (`recorridos` y `usuarios`) inician con los bytes `\xef\xbb\xbf` (UTF-8 BOM), requiriendo `encoding='utf-8-sig'` para no corromper el primer nombre de columna.
10. **Nomenclatura de estaciones**:
    - 2016 utiliza `domicilio_estacion_origen` y `domicilio_estacion_destino`.
    - 2019 y 2024 utilizan `direccion_estacion_origen` y `direccion_estacion_destino`.

#### B. Propuestas para Silver (a decidir por el grupo)
1. **Estandarización de IDs de usuario**:
   - Remover el sufijo `'BAEcobici'` en recorridos 2019 para transformarlo a entero.
   - Remover el sufijo `'.0'` (casteo a entero `Int64`) en recorridos 2024 para permitir el `JOIN` relacional exacto con la tabla de usuarios.
2. **Estrategia para recorridos 2016 sin IDs**:
   - Generar un identificador subrogado sintético (UUID v5 determinístico o hash SHA-256 de campos clave: origen, destino, fechas) para `id_recorrido`.
   - Documentar que los recorridos 2016 no podrán vincularse a perfiles individuales de usuarios, tratándose como mediciones agregadas/anónimas.
3. **Unificación de la duración del viaje**:
   - Homogeneizar `duracion_recorrido` a segundos enteros (`Int64`).
   - Evaluar si la duración se calcula directamente como la diferencia matemática `(fecha_destino - fecha_origen)` en segundos, descartando o contrastando el valor preexistente.
4. **Unificación temporal en usuarios**:
   - Concatenar y parsear `fecha_alta` + `hora_alta` en una única columna canónica `fecha_alta_usuario` de tipo `datetime64[ns]`.
5. **Estandarización de género y nombres de columnas**:
   - Renombrar las columnas de género en recorridos (`género`, `genero_usuario`) al nombre canónico `genero`.
   - Mapear los valores a un catálogo unificado: `M` -> `MALE`, `F` -> `FEMALE`, o definir siglas cortas consistentes (`M`, `F`, `O`).
6. **Depuración de columnas técnicas no operativas**:
   - Descartar la columna espuria `""` / `Unnamed: 0` al cargar recorridos 2019.
   - Estandarizar `domicilio_estacion_*` a `direccion_estacion_*`.
7. **Políticas de Cuarentena en Silver**:
   - Desviar a cuarentena viajes con duración negativa o superior a 24 horas (86.400 segundos).
   - Desviar a cuarentena viajes con fecha o estación de destino faltante.
   - Desviar a cuarentena usuarios con edades menores a 12 o mayores a 100 años, o aplicar reglas de imputación si se detecta que el valor corresponde al año de nacimiento (ej: `2024 - 2021 = 3 años` o descarte si sigue siendo menor a la edad habilitada).
