"""Capa Bronze: ingesta de datos crudos sin modificar."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"


def run() -> None:
    """Ejecuta la ingesta desde raw hacia bronze."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    # TODO: copiar o ingerir los archivos de RAW_DIR en BRONZE_DIR.
    print("Bronze: capa preparada.")


if __name__ == "__main__":
    run()
