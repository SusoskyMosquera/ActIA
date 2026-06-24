from __future__ import annotations
import time

from app.domain.models import AttributedSegment, Minutes


class DemoMinutesGenerator:
    """Demo adapter: returns a canned meeting-minutes (acta) in Spanish.

    Selected when ADAPTER_MODE=demo (the default). The participant count and
    duration are derived from the actual attributed transcript, so the output
    reflects its input even though the prose is canned.
    """

    def __init__(self, delay_seconds: float = 1.5) -> None:
        self._delay_seconds = delay_seconds

    def generate(self, transcript: list[AttributedSegment]) -> Minutes:
        if self._delay_seconds > 0:
            time.sleep(self._delay_seconds)

        speakers = sorted({segment.speaker for segment in transcript})
        duration = max((segment.end for segment in transcript), default=0.0)
        return Minutes(content=_build_acta(speakers, duration))


def _build_acta(speakers: list[str], duration_sec: float) -> str:
    participants = ", ".join(speakers) if speakers else "Sin oradores detectados"
    return f"""# Acta de Reunión

**Participantes:** {len(speakers)} oradores ({participants})
**Duración:** ~{duration_sec:.0f} segundos

## Resumen
Reunión de planificación para definir el alcance del primer sprint. Se acordaron
prioridades de desarrollo y la necesidad de una validación previa con el equipo
de seguridad.

## Temas tratados
- Definición del alcance del primer sprint.
- Prioridad: integración del módulo de pagos antes de fin de mes.
- Validación de requisitos con el equipo de seguridad.

## Decisiones
- Agendar una revisión con el equipo de seguridad para el miércoles.

## Compromisos
- Coordinar la reunión con el equipo de seguridad.
- Preparar la documentación técnica una vez confirmada la revisión.

## Próximos pasos
- Reencuentro el miércoles para revisar avances.

---
*Acta generada en modo demostración (datos de ejemplo).*
"""
