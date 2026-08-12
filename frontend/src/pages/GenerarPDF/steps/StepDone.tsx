import { AlertCircle, CheckCircle2, Download, RotateCcw } from 'lucide-react'
import { Card, CardBody } from '../../../components/ui/Card'
import Button from '../../../components/ui/Button'
import Spinner from '../../../components/ui/Spinner'
import type { FlowStep } from '../useGenerationFlow'

type StepDoneProps = {
  step: FlowStep
  progress: number
  statusText: string
  downloadUrl: string
  errorMessage: string
  driverName: string
  onRetry: () => void
  onReset: () => void
}

export default function StepDone({ step, progress, statusText, downloadUrl, errorMessage, driverName, onRetry, onReset }: StepDoneProps) {
  const filename = `${driverName.trim().replace(/\s+/g, '_') || 'inspeccion'}.pdf`

  if (step === 'uploading') {
    return (
      <Card>
        <CardBody className="pt-10 pb-10 text-center">
          <Spinner size="lg" className="mx-auto mb-3" />
          <p className="font-display text-base font-semibold text-fg mb-1">{statusText}</p>
          <div className="mx-auto mt-4 max-w-md">
            <div className="h-3 w-full overflow-hidden rounded-chip border border-border-strong bg-bg-subtle">
              <div
                className="h-full bg-signal-500 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="mt-2 font-mono text-xs font-bold text-fg-muted">{progress}%</p>
          </div>
        </CardBody>
      </Card>
    )
  }

  if (step === 'error') {
    return (
      <Card>
        <CardBody className="pt-10 pb-10 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-plate bg-stop-50 dark:bg-stop-900/20">
            <AlertCircle className="h-8 w-8 text-stop-600 dark:text-stop-300" />
          </div>
          <p className="mb-1 font-display text-lg font-bold uppercase tracking-[0.04em] text-fg">
            No se pudo generar el PDF
          </p>
          <p role="alert" className="mb-6 text-sm text-fg-muted">
            {errorMessage}
          </p>
          <Button onClick={onRetry}>
            <RotateCcw className="w-4 h-4" /> Intentar de nuevo
          </Button>
        </CardBody>
      </Card>
    )
  }

  return (
    <Card>
      <CardBody className="pt-10 pb-10 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-plate bg-signal-50 dark:bg-signal-900/20">
          <CheckCircle2 className="h-8 w-8 text-signal-600 dark:text-signal-300" />
        </div>
        <p className="mb-1 font-display text-lg font-bold uppercase tracking-[0.04em] text-fg">PDF generado</p>
        <p className="mb-6 font-mono text-sm text-fg-muted">{filename}</p>
        <div className="flex items-center justify-center gap-3">
          <Button variant="secondary" onClick={onReset}>
            <RotateCcw className="w-4 h-4" /> Nueva inspección
          </Button>
          <a
            href={downloadUrl}
            download={filename}
            className="plate-signal inline-flex items-center justify-center gap-2 rounded-plate px-5 py-2.5 text-sm font-bold uppercase tracking-[0.06em] transition-colors duration-150 hover:bg-signal-600 active:translate-y-px"
          >
            <Download className="h-4 w-4" /> Descargar PDF
          </a>
        </div>
      </CardBody>
    </Card>
  )
}
