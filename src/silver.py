"""Capa Silver: limpieza y estandarización de datos."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"


def run() -> None:
    """Transforma los datos de bronze en datos limpios de silver."""
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    # TODO: limpiar, tipar, validar y guardar datos en SILVER_DIR.
    print("Silver: capa preparada.")


if __name__ == "__main__":
    run()
