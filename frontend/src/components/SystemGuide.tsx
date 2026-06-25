interface GuideStep {
  title: string
  description: string
}

const STEPS: GuideStep[] = [
  {
    title: 'Subes el audio',
    description:
      'Arrastra la grabación de tu reunión o hacé clic para elegirla. Acepta los formatos de audio comunes (WAV, MP3, M4A…).',
  },
  {
    title: 'Se transcribe',
    description: 'El sistema convierte el audio en texto, palabra por palabra.',
  },
  {
    title: 'Se identifican los oradores',
    description:
      'Separa automáticamente quién dijo qué, sin que tengas que indicar cuántas personas hablaron.',
  },
  {
    title: 'Se genera el acta',
    description:
      'Un acta estructurada con resumen, temas tratados, decisiones, compromisos y próximos pasos.',
  },
]

export default function SystemGuide() {
  return (
    <section className="system-guide" aria-label="Cómo funciona ActIA">
      <h2>¿Cómo funciona?</h2>
      <p className="guide-intro">
        ActIA convierte la grabación de tu reunión en un acta estructurada. Solo
        subís el archivo — del resto se encarga el sistema.
      </p>

      <ol className="guide-steps">
        {STEPS.map((step, index) => (
          <li key={index} className="guide-step">
            <span className="guide-step-number" aria-hidden="true">
              {index + 1}
            </span>
            <div className="guide-step-body">
              <span className="guide-step-title">{step.title}</span>
              <span className="guide-step-desc">{step.description}</span>
            </div>
          </li>
        ))}
      </ol>

      <p className="guide-footer">
        El procesamiento corre en segundo plano: podés cancelarlo cuando quieras y
        un sonido te avisa cuando el acta está lista. El tiempo depende de la
        duración del audio.
      </p>
    </section>
  )
}
