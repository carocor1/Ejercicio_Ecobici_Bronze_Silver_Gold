"""Punto de entrada del pipeline de Ecobici."""

from src import bronze, gold, reportes, silver


def main() -> None:
    """Ejecuta las capas del pipeline en el orden establecido."""
    bronze.run()
    silver.run()
    gold.run()
    reportes.run()
    print("Pipeline finalizado correctamente.")


if __name__ == "__main__":
    main()
