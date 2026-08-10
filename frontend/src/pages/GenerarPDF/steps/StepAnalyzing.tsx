import { ScanLine } from 'lucide-react'
import { Card, CardBody } from '../../../components/ui/Card'

export default function StepAnalyzing({ statusText }: { statusText: string }) {
  return (
    <Card>
      <CardBody className="pt-10 pb-10 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-plate bg-plate-400">
          <ScanLine className="h-8 w-8 text-black" />
        </div>
        <p className="mb-1 font-display text-lg font-bold uppercase tracking-[0.04em] text-fg">
          {statusText || 'Analizando imágenes'}
        </p>
        <p className="mb-6 text-sm text-fg-muted">Lectura de placa y clasificación de posiciones</p>
        {/* Hazard tape: indeterminate on purpose — the backend reports per batch,
            so there is no honest percentage to show here. */}
        <div
          className="mx-auto h-3 max-w-md overflow-hidden rounded-chip border-2 border-border-strong bg-bg-subtle"
          role="progressbar"
          aria-label="Análisis en curso"
        >
          <div className="hazard-stripes h-full w-full animate-hazard" />
        </div>
      </CardBody>
    </Card>
  )
}
