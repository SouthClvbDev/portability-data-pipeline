"""Supuestos explícitos de capacidad para la simulación sintética."""

from datetime import date


# Escala (horas) de una Gamma de forma 3. Mayor escala implica más demoras.
# Los episodios se eligieron como situaciones de prueba, no como hechos reales.
INCIDENTS = {
    (2023, 10): ("sobrecarga de campaña", 24.0),
    (2024, 5): ("cambio de proceso", 26.0),
    (2025, 2): ("acumulación de pendientes", 22.0),
    (2026, 8): ("incidente de capacidad", 23.0),
}


def resolution_profile(day: date, volume_category: str = "normal") -> tuple[str, float]:
    """Devuelve escenario y escala sin depender de la hora de generación."""
    episode = INCIDENTS.get((day.year, day.month))
    if episode:
        return episode
    if day.year == 2023:
        scale = 14.5 if day.month <= 6 else 12.5
        stage = "estabilización inicial"
    elif day.year == 2024:
        scale = 11.5 if day.month <= 6 else 9.8
        stage = "ajustes de capacidad"
    else:
        scale = 8.2 if day.month <= 6 else 7.2
        stage = "proceso optimizado"
    if volume_category == "pico_positivo":
        return "pico de demanda", scale * 1.3
    if volume_category == "pico_negativo":
        return "demanda baja", scale * 0.88
    return stage, scale
