import { Eye, X } from 'lucide-react'
import Badge from '../../../components/ui/Badge'
import Select from '../../../components/ui/Select'
import { POSITIONS, SHORT_LABELS } from '../positions'
import type { ImageFile } from '../useImageQueue'

const confidenceTone = { high: 'success', medium: 'warning', low: 'neutral' } as const
const confidenceLabel = { high: 'Alta', medium: 'Media', low: 'Auto' } as const

type PhotoCardProps = {
  image: ImageFile
  onPreview: () => void
  onRemove: () => void
  onAssign?: (position: string) => void
  getCountForPosition?: (position: string) => number
}

export default function PhotoCard({ image, onPreview, onRemove, onAssign, getCountForPosition }: PhotoCardProps) {
  const options = onAssign
    ? POSITIONS.filter((p) => {
        const taken = getCountForPosition?.(p.value) ?? 0
        const isOwn = image.assignedPosition === p.value
        return isOwn || taken < p.max
      }).map((p) => {
        const taken = getCountForPosition?.(p.value) ?? 0
        const isOwn = image.assignedPosition === p.value
        const remaining = p.max - taken + (isOwn ? 1 : 0)
        const short = `${p.value.padStart(2, '0')} · ${SHORT_LABELS[p.value]}`
        return { value: p.value, label: `${short}${p.max > 1 ? ` (${remaining} disp.)` : ''}` }
      })
    : []

  return (
    <div className="group relative overflow-hidden rounded-plate border border-border bg-surface transition-colors duration-150 hover:border-signal-500">
      <div className="relative aspect-[4/3] w-full overflow-hidden bg-bg-subtle">
        <button
          onClick={onPreview}
          aria-label={`Ver ${image.file.name} en tamaño completo`}
          className="absolute inset-0 w-full h-full cursor-pointer"
        >
          <img src={image.preview} alt="" className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" />
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
            <Eye className="w-6 h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
          aria-label={`Quitar ${image.file.name}`}
          className="absolute right-2 top-2 rounded-chip bg-stop-500 p-1.5 text-white opacity-100 transition-opacity hover:bg-stop-600 md:opacity-0 md:group-focus-within:opacity-100 md:group-hover:opacity-100"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
      <div className="space-y-2 p-3">
        <p className="truncate font-mono text-[11px] text-fg-muted">{image.file.name}</p>
        {onAssign ? (
          <div className="flex items-center gap-2">
            {image.confidence && <Badge tone={confidenceTone[image.confidence]}>{confidenceLabel[image.confidence]}</Badge>}
            <div className="flex-1">
              <Select
                value={image.assignedPosition}
                onChange={onAssign}
                options={options}
                placeholder="— Posición —"
                aria-label={`Posición asignada a ${image.file.name}`}
                size="sm"
              />
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}
