"""Generación de reportes a partir de la capa Gold."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
REPORTES_DIR = GOLD_DIR / "reportes"


def run() -> None:
    """Genera los reportes finales a partir de la capa gold."""
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    REPORTES_DIR.mkdir(parents=True, exist_ok=True)
    # TODO: exportar tablas, gráficos o archivos de reporte en REPORTES_DIR.
    print("Reportes: capa preparada.")


if __name__ == "__main__":
    run()
