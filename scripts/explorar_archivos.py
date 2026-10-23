"""Script de exploración y verificación de archivos de datos crudos (Recorridos y Usuarios).

Tarea 1:
- PASO 3: Inspección estructural (nrows=1000, dtype=str), encodings, delimitadores,
          formatos de fecha/hora, duraciones, identificadores y rarezas.
- PASO 3b: Verificaciones sobre los archivos completos por chunks (chunksize=500_000):
          1. Ejemplos de ID de viaje y sufijos (o ausencia en 2016).
          2. Nulos o vacíos en campos clave.
          3. Fechas que no cumplen formato %Y-%m-%d %H:%M:%S.
          4. IDs de viaje duplicados.
          5. Viajes con fin anterior al inicio o duración > 86.400 segundos.
          6. Patrón de id_usuario (sufijo BAEcobici, .0, dígitos).
          Para usuarios: IDs nulos y duplicados sobre dataset completo.
"""

from datetime import datetime
import json
from pathlib import Path
import sys
import zipfile
import pandas as pd


# Configurar salida estándar en UTF-8 para entornos Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
OUTPUT_TXT = SCRIPTS_DIR / "salida_exploracion.txt"
OUTPUT_JSON = SCRIPTS_DIR / "salida_exploracion.json"

YEARS = [2016, 2019, 2024]


def detect_encoding_and_delimiter_from_bytes(raw_line: bytes) -> tuple[str, str]:
    """Detecta el encoding y el delimitador (, o ;) a partir de la primera línea cruda."""
    if raw_line.startswith(b"\xef\xbb\xbf"):
        encoding = "utf-8-sig"
    else:
        try:
            raw_line.decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            encoding = "latin-1"

    decoded_line = raw_line.decode(encoding, errors="replace")

    commas = decoded_line.count(",")
    semicolons = decoded_line.count(";")
    delimiter = "," if commas >= semicolons else ";"

    return encoding, delimiter


def deduce_strptime_format(sample_values: list[str]) -> str:
    """Deduce el patrón strptime a partir de una lista de valores de ejemplo."""
    candidates = [
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d-%m-%y",
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%I:%M:%S %p",
        "%H:%M:%S",
    ]
    for fmt in candidates:
        all_match = True
        for val in sample_values:
            try:
                datetime.strptime(val.strip(), fmt)
            except ValueError:
                all_match = False
                break
        if all_match:
            return fmt
    return "Formato variable / no estándar"


def find_file_by_year(pattern_prefix: str, year: int, extension: str) -> Path | None:
    """Localiza un archivo por año y extensión usando patrón glob."""
    pattern = f"*{pattern_prefix}*{year}*.{extension}"
    matches = list(RAW_DIR.glob(pattern))
    if not matches:
        matches = list(RAW_DIR.glob(f"*{year}*.{extension}"))
    return matches[0] if matches else None


def analyze_recorridos_file(zip_path: Path, year: int) -> dict:
    """Analiza un archivo comprimido de recorridos (PASO 3 y PASO 3b)."""
    info = {
        "anio": year,
        "tipo": "RECORRIDOS",
        "archivo_origen": zip_path.name,
    }

    with zipfile.ZipFile(zip_path, "r") as zf:
        # a) Archivos dentro del ZIP
        all_members = zf.namelist()
        csv_members = [m for m in all_members if m.lower().endswith(".csv")]
        data_csv = csv_members[0] if csv_members else all_members[0]

        info["archivos_en_zip"] = all_members
        info["csv_datos"] = data_csv

        # b) Separador y encoding
        with zf.open(data_csv) as f_raw:
            first_raw_line = f_raw.readline()
        encoding, sep = detect_encoding_and_delimiter_from_bytes(first_raw_line)
        info["encoding_detectado"] = encoding
        info["separador_detectado"] = sep

        # Lectura de muestra inicial (nrows=1000)
        with zf.open(data_csv) as f_sample:
            df_sample = pd.read_csv(
                f_sample,
                nrows=1000,
                sep=sep,
                encoding=encoding,
                dtype=str,
            )

        # c) Nombres exactos de columnas
        columnas = list(df_sample.columns)
        info["columnas"] = columnas

        # d) Formato de fecha y hora en muestra
        date_cols = [c for c in columnas if "fecha" in c.lower() or "hora" in c.lower()]
        info["fechas"] = {}
        for c in date_cols:
            clean_samples = df_sample[c].dropna().head(3).tolist()
            fmt = deduce_strptime_format(clean_samples) if clean_samples else "Sin datos"
            info["fechas"][c] = {
                "ejemplos": clean_samples,
                "formato_deducido": fmt,
            }

        # e) Duración del viaje
        dur_cols = [c for c in columnas if "duracion" in c.lower() or "tiempo" in c.lower()]
        if dur_cols:
            col_dur = dur_cols[0]
            ejemplos_dur = df_sample[col_dur].dropna().head(3).tolist()
            if year == 2016:
                unidad = "Texto con formato de duración timedelta ('0 days HH:MM:SS.ns')"
            elif year == 2019:
                unidad = "Segundos representados en texto con coma como separador de miles (ej: '2,814')"
            else:
                unidad = "Segundos expresados como valor entero numérico en texto (ej: '568')"
            info["duracion"] = {
                "columna": col_dur,
                "trae_duracion": True,
                "unidad_estimada": unidad,
                "ejemplos": ejemplos_dur,
            }
        else:
            info["duracion"] = {"trae_duracion": False, "descripcion": "No trae columna de duración"}

        # f) ID de usuario en muestra
        user_id_cols = [c for c in columnas if "usuario" in c.lower() and "id" in c.lower()]
        if user_id_cols:
            col_uid = user_id_cols[0]
            nulos_muestra = int(df_sample[col_uid].isna().sum())
            ejemplos_uid = df_sample[col_uid].dropna().head(3).tolist()
            info["id_usuario"] = {
                "trae_id_usuario": True,
                "columna": col_uid,
                "nulos_en_muestra_1000": nulos_muestra,
                "ejemplos": ejemplos_uid,
            }
        else:
            info["id_usuario"] = {
                "trae_id_usuario": False,
                "descripcion": "No contiene columna de id de usuario (solo trae 'genero_usuario')",
            }

        # PASO 3b: Verificaciones sobre dataset completo por chunks
        print(f"  [PASO 3b] Ejecutando verificaciones completas en chunks para {zip_path.name}...")
        trip_col = "Id_recorrido" if "Id_recorrido" in columnas else ("id_recorrido" if "id_recorrido" in columnas else None)
        user_col = user_id_cols[0] if user_id_cols else None

        total_filas = 0
        seen_trip_ids = set()
        dup_trip_ids = 0
        trip_id_samples = []

        nulos_clave = {
            "id_usuario": 0 if user_col else "No existe columna en este año",
            "id_estacion_origen": 0,
            "id_estacion_destino": 0,
            "fecha_origen_recorrido": 0,
            "fecha_destino_recorrido": 0,
        }

        fechas_invalidas_origen = 0
        fechas_invalidas_destino = 0
        viajes_fin_anterior = 0
        viajes_duracion_mayor_86400 = 0

        patron_usuario = {
            "sufijo_BAEcobici": 0,
            "terminan_en_punto_cero": 0,
            "solo_digitos": 0,
            "otros": 0,
        }

        with zf.open(data_csv) as f_full:
            reader = pd.read_csv(
                f_full,
                sep=sep,
                encoding="utf-8-sig",
                dtype=str,
                chunksize=500_000,
            )
            for chunk in reader:
                total_filas += len(chunk)

                # 1 y 4. ID de viaje: muestras y duplicados
                if trip_col:
                    if len(trip_id_samples) < 5:
                        remaining = 5 - len(trip_id_samples)
                        trip_id_samples.extend(chunk[trip_col].dropna().head(remaining).tolist())
                    for val in chunk[trip_col]:
                        if val in seen_trip_ids:
                            dup_trip_ids += 1
                        else:
                            seen_trip_ids.add(val)

                # 2. Nulos o vacíos en campos requeridos
                for campo in ["id_estacion_origen", "id_estacion_destino", "fecha_origen_recorrido", "fecha_destino_recorrido"]:
                    if campo in chunk.columns:
                        nulos_clave[campo] += int((chunk[campo].isna() | (chunk[campo].str.strip() == "")).sum())

                if user_col:
                    nulos_clave["id_usuario"] += int((chunk[user_col].isna() | (chunk[user_col].str.strip() == "")).sum())

                # 3 y 5. Análisis de fechas (formato y consistencia temporal)
                dt_origen = pd.to_datetime(chunk["fecha_origen_recorrido"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
                dt_destino = pd.to_datetime(chunk["fecha_destino_recorrido"], format="%Y-%m-%d %H:%M:%S", errors="coerce")

                orig_no_nulo = chunk["fecha_origen_recorrido"].notna() & (chunk["fecha_origen_recorrido"].str.strip() != "")
                dest_no_nulo = chunk["fecha_destino_recorrido"].notna() & (chunk["fecha_destino_recorrido"].str.strip() != "")

                fechas_invalidas_origen += int((orig_no_nulo & dt_origen.isna()).sum())
                fechas_invalidas_destino += int((dest_no_nulo & dt_destino.isna()).sum())

                valid_dts = dt_origen.notna() & dt_destino.notna()
                diff_sec = (dt_destino[valid_dts] - dt_origen[valid_dts]).dt.total_seconds()
                viajes_fin_anterior += int((diff_sec < 0).sum())
                viajes_duracion_mayor_86400 += int((diff_sec > 86400).sum())

                # 6. Patrones de id_usuario
                if user_col:
                    u_clean = chunk[user_col].dropna()
                    u_clean = u_clean[u_clean.str.strip() != ""]
                    m_bae = u_clean.str.endswith("BAEcobici")
                    m_dot0 = u_clean.str.endswith(".0")
                    m_digits = u_clean.str.isdigit()
                    m_other = ~(m_bae | m_dot0 | m_digits)
                    patron_usuario["sufijo_BAEcobici"] += int(m_bae.sum())
                    patron_usuario["terminan_en_punto_cero"] += int(m_dot0.sum())
                    patron_usuario["solo_digitos"] += int(m_digits.sum())
                    patron_usuario["otros"] += int(m_other.sum())

        info["total_filas"] = total_filas

        # Detalle de PASO 3b
        if trip_col:
            tiene_sufijo = all(str(x).endswith("BAEcobici") for x in trip_id_samples)
            sufijo_desc = "SÍ, contiene sufijo 'BAEcobici'" if tiene_sufijo else "NO posee sufijo alfanumérico (solo dígitos)"
        else:
            sufijo_desc = "No aplica: NO existe ninguna columna que sirva de ID de viaje en 2016"

        info["verificaciones_paso_3b"] = {
            "columna_id_viaje": trip_col if trip_col else "Ninguna (no existe)",
            "ejemplos_id_viaje": trip_id_samples,
            "analisis_sufijo_id_viaje": sufijo_desc,
            "nulos_o_vacios": nulos_clave,
            "fechas_formato_invalido": {
                "fecha_origen_recorrido": fechas_invalidas_origen,
                "fecha_destino_recorrido": fechas_invalidas_destino,
            },
            "id_viaje_duplicados": dup_trip_ids if trip_col else "No aplica (sin columna de id)",
            "viajes_fin_anterior_al_inicio": viajes_fin_anterior,
            "viajes_duracion_mayor_86400s": viajes_duracion_mayor_86400,
            "patron_id_usuario": patron_usuario if user_col else "No aplica (sin columna id_usuario)",
        }

        # i) Rarezas detectadas
        rarezas = []
        if any(c.startswith("Unnamed") for c in columnas):
            rarezas.append("Columna espuria 'Unnamed: 0' generada por exportación de pandas con índice.")
        if first_raw_line.startswith(b"\xef\xbb\xbf"):
            rarezas.append("Archivo con marca BOM UTF-8 (\\xef\\xbb\\xbf).")
        if not user_id_cols:
            rarezas.append("No tiene id_usuario, imposibilitando cruzar viajes con la tabla de usuarios de 2016.")
        if "Id_recorrido" in columnas:
            rarezas.append("Columna 'Id_recorrido' con 'I' mayúscula y valores alfanuméricos sufijados con 'BAEcobici'.")
        if not trip_col:
            rarezas.append("No posee ningún identificador primario de viaje (id_recorrido).")
        if "género" in columnas:
            rarezas.append("Columna de género con tilde ('género') en minúsculas.")
        if "genero_usuario" in columnas:
            rarezas.append("Columna de género nombrada 'genero_usuario' en el dataset de recorridos.")
        if "domicilio_estacion_origen" in columnas:
            rarezas.append("Usa 'domicilio_estacion_*' en lugar de 'direccion_estacion_*'.")
        if nulos_clave["fecha_destino_recorrido"] > 0:
            rarezas.append(f"Se registraron {nulos_clave['fecha_destino_recorrido']:,} viajes sin fecha de destino (nulos).")
        if nulos_clave["id_estacion_destino"] not in [0, "No existe columna en este año"] and nulos_clave["id_estacion_destino"] > 0:
            rarezas.append(f"Se registraron {nulos_clave['id_estacion_destino']:,} viajes sin estación de destino (nulos).")
        if dup_trip_ids > 0:
            rarezas.append(f"Se detectó {dup_trip_ids} id_recorrido duplicado en el dataset.")
        if viajes_duracion_mayor_86400 > 0:
            rarezas.append(f"Se registraron {viajes_duracion_mayor_86400:,} viajes con duración calculada mayor a 24 horas (86.400s).")

        info["rarezas"] = rarezas

    return info


def analyze_usuarios_file(csv_path: Path, year: int) -> dict:
    """Analiza un archivo de usuarios en CSV (PASO 3 y PASO 3b)."""
    info = {
        "anio": year,
        "tipo": "USUARIOS",
        "archivo_origen": csv_path.name,
    }

    info["nombre_csv"] = csv_path.name

    # b) Separador y encoding
    with open(csv_path, "rb") as f_raw:
        first_raw_line = f_raw.readline()
    encoding, sep = detect_encoding_and_delimiter_from_bytes(first_raw_line)
    info["encoding_detectado"] = encoding
    info["separador_detectado"] = sep

    # Muestra de 1000 filas
    df_sample = pd.read_csv(
        csv_path,
        nrows=1000,
        sep=sep,
        encoding=encoding,
        dtype=str,
    )

    columnas = list(df_sample.columns)
    info["columnas"] = columnas

    # Formatos de fecha y hora
    date_cols = [c for c in columnas if "fecha" in c.lower() or "hora" in c.lower()]
    info["fechas"] = {}
    for c in date_cols:
        clean_samples = df_sample[c].dropna().head(3).tolist()
        fmt = deduce_strptime_format(clean_samples) if clean_samples else "Sin datos"
        info["fechas"][c] = {
            "ejemplos": clean_samples,
            "formato_deducido": fmt,
        }

    info["duracion"] = {
        "trae_duracion": False,
        "descripcion": "No aplica. Dataset de registro de usuarios (no de recorridos).",
    }

    user_id_cols = [c for c in columnas if "usuario" in c.lower() and "id" in c.lower()]
    col_uid = user_id_cols[0] if user_id_cols else "id_usuario"
    nulos_muestra = int(df_sample[col_uid].isna().sum()) if col_uid in df_sample.columns else 0
    ejemplos_uid = df_sample[col_uid].dropna().head(3).tolist() if col_uid in df_sample.columns else []

    info["id_usuario"] = {
        "trae_id_usuario": True if user_id_cols else False,
        "columna": col_uid,
        "nulos_en_muestra_1000": nulos_muestra,
        "ejemplos": ejemplos_uid,
    }

    # PASO 3b y conteo global por chunks
    print(f"  [PASO 3b] Ejecutando verificaciones completas en chunks para {csv_path.name}...")
    total_filas = 0
    genero_counts = {}
    edades_numericas = []
    edades_nulas = 0

    seen_user_ids = set()
    dup_user_ids = 0
    null_user_ids = 0

    reader = pd.read_csv(
        csv_path,
        sep=sep,
        encoding="utf-8-sig",
        dtype=str,
        chunksize=500_000,
    )

    col_genero = [c for c in columnas if "genero" in c.lower()][0]
    col_edad = [c for c in columnas if "edad" in c.lower()][0]

    for chunk in reader:
        total_filas += len(chunk)

        # Verificación de id_usuario completo: nulos y duplicados
        null_user_ids += int((chunk[col_uid].isna() | (chunk[col_uid].str.strip() == "")).sum())
        for val in chunk[col_uid]:
            if val in seen_user_ids:
                dup_user_ids += 1
            else:
                seen_user_ids.add(val)

        # value_counts género
        vc = chunk[col_genero].value_counts(dropna=False).to_dict()
        for k, v in vc.items():
            label = "NaN / Nulo" if pd.isna(k) else str(k)
            genero_counts[label] = genero_counts.get(label, 0) + int(v)

        # Edades numéricas
        num_series = pd.to_numeric(chunk[col_edad], errors="coerce")
        edades_nulas += int(num_series.isna().sum())
        clean_num = num_series.dropna()
        if not clean_num.empty:
            edades_numericas.append((float(clean_num.min()), float(clean_num.max())))

    info["total_filas"] = total_filas

    min_edad = min(pair[0] for pair in edades_numericas) if edades_numericas else None
    max_edad = max(pair[1] for pair in edades_numericas) if edades_numericas else None

    info["metricas_usuarios"] = {
        "columna_genero": col_genero,
        "distribucion_genero": genero_counts,
        "columna_edad": col_edad,
        "edad_minima": min_edad,
        "edad_maxima": max_edad,
        "edades_nulas_o_invalidas": edades_nulas,
    }

    info["verificaciones_paso_3b"] = {
        "columna_id_usuario": col_uid,
        "ids_nulos_o_vacios": null_user_ids,
        "ids_duplicados": dup_user_ids,
    }

    # Rarezas
    rarezas = []
    if "ID_usuario" in columnas:
        rarezas.append("Nombre de columna 'ID_usuario' con prefijo en mayúsculas 'ID' en lugar de minúsculas.")
    if first_raw_line.startswith(b"\xef\xbb\xbf"):
        rarezas.append("Archivo con marca BOM UTF-8 (\\xef\\xbb\\xbf).")
    if max_edad is not None and max_edad > 120:
        rarezas.append(f"Valores inverosímiles en edad: valor máximo encontrado de {max_edad} años.")
    if min_edad is not None and min_edad < 10:
        rarezas.append(f"Valores inverosímiles en edad: valor mínimo encontrado de {min_edad} años.")
    if edades_nulas > 0:
        rarezas.append(f"Se registraron {edades_nulas} registros con edad nula o no numérica.")
    if "NaN / Nulo" in genero_counts:
        rarezas.append(f"Se registraron {genero_counts['NaN / Nulo']} usuarios con género nulo.")

    info["rarezas"] = rarezas

    return info


def format_report_text(results: list[dict]) -> str:
    """Construye un reporte en formato texto legible con todas las secciones de PASO 3 y PASO 3b."""
    lines = []
    lines.append("=" * 80)
    lines.append("INFORME DE EXPLORACIÓN Y VERIFICACIÓN COMPLETA - DATASET ECOBICI")
    lines.append(f"Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append("")

    for item in results:
        tipo = item["tipo"]
        anio = item["anio"]
        archivo = item["archivo_origen"]

        lines.append("=" * 80)
        lines.append(f"[{tipo} {anio}] Archivo: {archivo}")
        lines.append("=" * 80)

        # PASO 3
        lines.append("\n--- PARTE 1: EXPLORACIÓN ESTRUCTURAL (Muestra inicial nrows=1000) ---")
        if tipo == "RECORRIDOS":
            lines.append(f"a) Archivos en ZIP: {item['archivos_en_zip']}")
            lines.append(f"   CSV de datos identificado: {item['csv_datos']}")
        else:
            lines.append(f"a) Nombre del archivo CSV: {item['nombre_csv']}")

        lines.append(f"b) Separador detectado: '{item['separador_detectado']}'")
        lines.append(f"   Encoding con el que se pudo leer: {item['encoding_detectado']}")

        lines.append(f"c) Nombres exactos de las columnas ({len(item['columnas'])}):")
        for col in item["columnas"]:
            lines.append(f"      - {col}")

        lines.append("d) Formato de fecha y hora:")
        for col, data in item["fechas"].items():
            lines.append(f"      - Columna '{col}':")
            lines.append(f"          Ejemplos: {data['ejemplos']}")
            lines.append(f"          Formato strptime deducido: {data['formato_deducido']}")

        lines.append("e) Duración del viaje:")
        dur = item["duracion"]
        if dur["trae_duracion"]:
            lines.append(f"      - Columna: '{dur['columna']}'")
            lines.append(f"      - Unidad / formato: {dur['unidad_estimada']}")
            lines.append(f"      - Ejemplos: {dur['ejemplos']}")
        else:
            lines.append(f"      - {dur['descripcion']}")

        lines.append("f) ID de usuario en muestra:")
        uid = item["id_usuario"]
        if uid["trae_id_usuario"]:
            lines.append(f"      - Columna: '{uid['columna']}'")
            lines.append(f"      - Nulos en muestra (primeras 1000 filas): {uid['nulos_en_muestra_1000']}")
            lines.append(f"      - Ejemplos: {uid['ejemplos']}")
        else:
            lines.append(f"      - {uid['descripcion']}")

        lines.append(f"g) Cantidad TOTAL de filas (sin encabezado): {item['total_filas']:,}")

        if "metricas_usuarios" in item:
            mu = item["metricas_usuarios"]
            lines.append("h) Métricas de Usuarios sobre archivo completo:")
            lines.append(f"      - Distribución de género ({mu['columna_genero']}):")
            for cat, cnt in mu["distribucion_genero"].items():
                lines.append(f"          * {cat}: {cnt:,}")
            lines.append(f"      - Rango de edades ({mu['columna_edad']}):")
            lines.append(f"          * Mínimo: {mu['edad_minima']}")
            lines.append(f"          * Máximo: {mu['edad_maxima']}")
            lines.append(f"          * Nulos / no numéricos: {mu['edades_nulas_o_invalidas']:,}")

        lines.append("\n--- PARTE 2: VERIFICACIONES SOBRE ARCHIVOS COMPLETOS (PASO 3b) ---")
        v3b = item["verificaciones_paso_3b"]
        if tipo == "RECORRIDOS":
            lines.append("1. Ejemplos de ID de viaje y análisis de sufijos:")
            lines.append(f"      - Columna: {v3b['columna_id_viaje']}")
            lines.append(f"      - 5 Ejemplos: {v3b['ejemplos_id_viaje']}")
            lines.append(f"      - Diagnóstico de sufijo: {v3b['analisis_sufijo_id_viaje']}")

            lines.append("2. Cantidad de nulos o vacíos en campos clave:")
            for k, v in v3b["nulos_o_vacios"].items():
                val_str = f"{v:,}" if isinstance(v, int) else str(v)
                lines.append(f"      - {k}: {val_str}")

            lines.append("3. Cantidad de fechas que NO cumplen formato %Y-%m-%d %H:%M:%S:")
            lines.append(f"      - fecha_origen_recorrido: {v3b['fechas_formato_invalido']['fecha_origen_recorrido']}")
            lines.append(f"      - fecha_destino_recorrido: {v3b['fechas_formato_invalido']['fecha_destino_recorrido']}")

            lines.append("4. Cantidad de IDs de viaje duplicados:")
            dup_val = f"{v3b['id_viaje_duplicados']:,}" if isinstance(v3b["id_viaje_duplicados"], int) else str(v3b["id_viaje_duplicados"])
            lines.append(f"      - Duplicados encontrados: {dup_val}")

            lines.append("5. Consistencia temporal de viajes (calculada con fechas):")
            lines.append(f"      - Viajes con fin anterior al inicio (destino < origen): {v3b['viajes_fin_anterior_al_inicio']:,}")
            lines.append(f"      - Viajes con duración mayor a 86.400 segundos (> 24 hs): {v3b['viajes_duracion_mayor_86400s']:,}")

            lines.append("6. Patrón de id_usuario en los datos completos:")
            if isinstance(v3b["patron_id_usuario"], dict):
                for pk, pv in v3b["patron_id_usuario"].items():
                    lines.append(f"      - {pk}: {pv:,}")
            else:
                lines.append(f"      - {v3b['patron_id_usuario']}")

        else:
            lines.append("Verificaciones de ID de usuario en archivo completo:")
            lines.append(f"      - Columna evaluada: {v3b['columna_id_usuario']}")
            lines.append(f"      - IDs nulos o vacíos: {v3b['ids_nulos_o_vacios']:,}")
            lines.append(f"      - IDs duplicados: {v3b['ids_duplicados']:,}")

        lines.append("\n--- PARTE 3: RAREZAS Y ANOMALÍAS DETECTADAS (i) ---")
        if item["rarezas"]:
            for r in item["rarezas"]:
                lines.append(f"      [!] {r}")
        else:
            lines.append("      (Ninguna anomalía crítica detectada)")

        lines.append("\n")

    return "\n".join(lines)


def main() -> None:
    """Función orquestadora de la exploración y verificación completa."""
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    print("Iniciando exploración y verificación (PASO 3 + PASO 3b) en data/raw...\n")

    for year in YEARS:
        # Explorar Recorridos (ZIP)
        zip_file = find_file_by_year("recorridos", year, "zip")
        if zip_file:
            print(f"Procesando Recorridos {year} ({zip_file.name})...")
            rec_res = analyze_recorridos_file(zip_file, year)
            results.append(rec_res)
        else:
            print(f"ADVERTENCIA: No se encontró archivo ZIP para recorridos {year}.")

        # Explorar Usuarios (CSV)
        csv_file = find_file_by_year("usuarios", year, "csv")
        if csv_file:
            print(f"Procesando Usuarios {year} ({csv_file.name})...")
            usr_res = analyze_usuarios_file(csv_file, year)
            results.append(usr_res)
        else:
            print(f"ADVERTENCIA: No se encontró archivo CSV para usuarios {year}.")

    # Generar texto de reporte
    report_text = format_report_text(results)

    # Imprimir en consola
    print("\n" + report_text)

    # Guardar en archivo TXT
    OUTPUT_TXT.write_text(report_text, encoding="utf-8")
    print(f"\nReporte guardado exitosamente en: {OUTPUT_TXT}")

    # Guardar también en JSON estructurado
    OUTPUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Datos estructurados guardados en: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
