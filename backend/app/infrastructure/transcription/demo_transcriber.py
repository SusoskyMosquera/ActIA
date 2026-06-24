from __future__ import annotations
import time

from app.domain.models import TranscriptSegment

# A short, canned Spanish planning meeting. Lets the full pipeline run
# end-to-end without faster-whisper / torch installed.
_DEMO_SEGMENTS: list[tuple[float, float, str]] = [
    (0.0, 4.5, "Buenos días a todos, gracias por conectarse. El objetivo de hoy es definir el alcance del primer sprint."),
    (4.5, 9.0, "Perfecto. Desde mi lado, la prioridad es cerrar la integración del módulo de pagos antes de fin de mes."),
    (9.0, 13.5, "De acuerdo, aunque deberíamos validar primero los requisitos con el equipo de seguridad."),
    (13.5, 18.0, "Buen punto. Agendemos esa revisión para el miércoles. ¿Quién puede coordinarla?"),
    (18.0, 22.0, "Yo me encargo de coordinar la reunión con seguridad."),
    (22.0, 27.0, "Entonces quedo a la espera de la confirmación para preparar la documentación técnica."),
    (27.0, 31.0, "Excelente. Cerramos con esos compromisos y nos vemos el miércoles."),
]


class DemoTranscriber:
    """Demo adapter: returns a canned Spanish transcript.

    Selected when ADAPTER_MODE=demo (the default). The optional delay makes
    the polling UI show real progress; tests construct it with delay 0.
    """

    def __init__(self, delay_seconds: float = 1.5) -> None:
        self._delay_seconds = delay_seconds

    def transcribe(self, audio_path: str) -> list[TranscriptSegment]:
        if self._delay_seconds > 0:
            time.sleep(self._delay_seconds)
        return [
            TranscriptSegment(start=start, end=end, text=text)
            for start, end, text in _DEMO_SEGMENTS
        ]
