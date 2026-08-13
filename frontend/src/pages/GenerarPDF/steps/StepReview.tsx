import { AlertCircle, CheckCircle2 } from 'lucide-react'
import { Card, CardBody } from '../../../components/ui/Card'
import EmptyState from '../../../components/ui/EmptyState'
import PhotoCard from '../components/PhotoCard'
import PositionMap from '../components/PositionMap'
import type { ImageFile } from '../useImageQueue'

type StepReviewProps = {
  images: ImageFile[]
  onAssign: (id: string, position: string) => void
  onRemove: (id: string) => void
  getCountForPosition: (position: string) => number
  onPreview: (preview: string, filename: string) => void
  errorMessage: string
}

export default function StepReview({ images, onAssign, onRemove, getCountForPosition, onPreview, errorMessage }: StepReviewProps) {
  // Assigned photos already show connected to the vehicle in the map above —
  // this tray is only for what's left to place, so nothing appears twice.
  const pending = images.filter((img) => !img.assignedPosition)

  return (
    <div className="space-y-6">
      <PositionMap images={images} onAssign={onAssign} />

      <Card>
        <CardBody className="pt-6">
          <div className="mb-4 flex items-baseline justify-between gap-3">
            <h3 className="font-display text-sm font-bold uppercase tracking-[0.08em] text-fg">
              Sin asignar · {pending.length}
            </h3>
            {pending.length > 0 && (
              <p className="text-xs text-fg-muted">
                Toque un espacio del mapa o elija posición aquí abajo.
              </p>
            )}
          </div>

          {pending.length === 0 ? (
            <EmptyState icon={CheckCircle2} title="Todas las fotos tienen posición" />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {pending.map((img) => (
                <PhotoCard
                  key={img.id}
                  image={img}
                  onPreview={() => onPreview(img.preview, img.file.name)}
                  onRemove={() => onRemove(img.id)}
                  onAssign={(position) => onAssign(img.id, position)}
                  getCountForPosition={getCountForPosition}
                />
              ))}
            </div>
          )}

          {errorMessage && (
            <div
              role="alert"
              className="mt-5 flex items-start gap-3 rounded-plate border border-stop-200 bg-stop-50 p-4 dark:border-stop-800 dark:bg-stop-900/20"
            >
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-stop-500" />
              <p className="text-sm font-semibold text-stop-700 dark:text-stop-200">{errorMessage}</p>
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  )
}
