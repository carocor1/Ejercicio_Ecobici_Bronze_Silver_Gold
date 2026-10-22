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
