"""Capa Gold: datos agregados y listos para análisis."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"


def run() -> None:
    """Genera tablas analíticas desde los datos silver."""
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    # TODO: crear métricas, agregados y datasets finales en GOLD_DIR.
    print("Gold: capa preparada.")


if __name__ == "__main__":
    run()
