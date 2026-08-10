import { AlertCircle } from 'lucide-react'
import { Card, CardBody } from '../../../components/ui/Card'
import PhotoCard from '../components/PhotoCard'
import PositionMap from '../components/PositionMap'
import type { ImageFile } from '../useImageQueue'

const confidenceRank = { low: 0, medium: 1, high: 2, undefined: -1 } as const

type StepReviewProps = {
  images: ImageFile[]
  onAssign: (id: string, position: string) => void
  onRemove: (id: string) => void
  getCountForPosition: (position: string) => number
  onPreview: (preview: string, filename: string) => void
  errorMessage: string
}

export default function StepReview({ images, onAssign, onRemove, getCountForPosition, onPreview, errorMessage }: StepReviewProps) {
  const sorted = [...images].sort((a, b) => confidenceRank[a.confidence ?? 'undefined'] - confidenceRank[b.confidence ?? 'undefined'])

  return (
    <div className="space-y-6">
      <PositionMap images={images} onAssign={onAssign} />

      <Card>
        <CardBody className="pt-6">
          <p className="mb-4 text-xs text-fg-muted">
            Las fotos con confianza <span className="font-bold text-plate-600 dark:text-plate-300">Media</span> o{' '}
            <span className="font-bold text-fg">Auto</span> aparecen primero: revíselas con atención.
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {sorted.map((img) => (
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

          {errorMessage && (
            <div
              role="alert"
              className="mt-5 flex items-start gap-3 rounded-plate border-2 border-stop-500 bg-stop-50 p-4 dark:bg-stop-900/20"
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
