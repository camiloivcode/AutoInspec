import { useState } from 'react'
import * as Popover from '@radix-ui/react-popover'
import { Check } from 'lucide-react'
import { POSITIONS, SPATIAL_NODES, NON_SPATIAL, SHORT_LABELS } from '../positions'
import type { ImageFile } from '../useImageQueue'

type PositionMapProps = {
  images: ImageFile[]
  onAssign: (imageId: string, position: string) => void
}

function stateClasses(filled: number, max: number) {
  if (filled === 0) return 'border-border-strong bg-surface text-fg-subtle'
  if (filled < max) return 'border-plate-600 bg-plate-400 text-black'
  return 'border-signal-700 bg-signal-500 text-white'
}

/**
 * The inspector physically walks around the vehicle, so the six angular
 * positions are shown where they actually are. Documents, driver and the road
 * kit have no place on the body and stay in a separate row rather than being
 * pinned to the diagram for decoration.
 */
export default function PositionMap({ images, onAssign }: PositionMapProps) {
  const [open, setOpen] = useState<string | null>(null)

  const byPosition = (pos: string) => images.filter((img) => img.assignedPosition === pos)
  const unassigned = images.filter((img) => !img.assignedPosition)
  const covered = POSITIONS.filter((p) => byPosition(p.value).length > 0).length

  function renderNode(pos: string, label: string, extraClass: string, style?: React.CSSProperties) {
    const def = POSITIONS.find((p) => p.value === pos)!
    const filled = byPosition(pos.toString())
    const isOpen = open === pos

    return (
      <Popover.Root key={pos} open={isOpen} onOpenChange={(next) => setOpen(next ? pos : null)}>
        <Popover.Trigger asChild>
          <button
            style={style}
            aria-label={`Posición ${pos}, ${def.label.replace(/^\d+\.\s*/, '')}, ${
              filled.length === 0 ? 'sin asignar' : `${filled.length} de ${def.max} asignada`
            }`}
            className={`flex items-center gap-1.5 rounded-chip border-2 px-2 py-1 font-mono text-[11px] font-bold transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-500 focus-visible:ring-offset-2 focus-visible:ring-offset-bg ${stateClasses(
              filled.length,
              def.max
            )} ${extraClass}`}
          >
            <span>{pos.padStart(2, '0')}</span>
            <span className="hidden font-body font-bold uppercase tracking-[0.04em] sm:inline">{label}</span>
            {def.max > 1 && <span className="opacity-80">{filled.length}/{def.max}</span>}
            {filled.length >= def.max && <Check className="h-3 w-3" />}
          </button>
        </Popover.Trigger>
        <Popover.Portal>
          <Popover.Content
            sideOffset={6}
            className="plate z-50 w-60 p-2 focus:outline-none"
            aria-label={`Asignar foto a ${def.label}`}
          >
            <p className="mb-2 px-1 text-[11px] font-bold uppercase tracking-[0.08em] text-fg-muted">{def.label}</p>
            <div className="max-h-56 space-y-1 overflow-y-auto">
              {filled.map((img) => (
                <button
                  key={img.id}
                  onClick={() => {
                    onAssign(img.id, '')
                    setOpen(null)
                  }}
                  className="flex w-full items-center gap-2 rounded-chip bg-signal-500 p-1 text-left text-white transition-colors hover:bg-signal-600"
                >
                  <img src={img.preview} alt="" className="h-8 w-8 shrink-0 rounded-[3px] object-cover" />
                  <span className="min-w-0 flex-1 truncate font-mono text-[11px]">{img.file.name}</span>
                  <span className="shrink-0 pr-1 text-[10px] font-bold uppercase">Quitar</span>
                </button>
              ))}

              {filled.length >= def.max ? (
                <p className="px-1 py-2 text-[11px] text-fg-subtle">
                  Posición completa. Quite una foto para cambiarla.
                </p>
              ) : unassigned.length === 0 ? (
                <p className="px-1 py-2 text-[11px] text-fg-subtle">No hay fotos sin asignar.</p>
              ) : (
                unassigned.map((img) => (
                  <button
                    key={img.id}
                    onClick={() => {
                      onAssign(img.id, pos)
                      setOpen(null)
                    }}
                    className="flex w-full items-center gap-2 rounded-chip p-1 text-left transition-colors hover:bg-bg-subtle"
                  >
                    <img src={img.preview} alt="" className="h-8 w-8 shrink-0 rounded-[3px] object-cover" />
                    <span className="min-w-0 flex-1 truncate font-mono text-[11px] text-fg">{img.file.name}</span>
                  </button>
                ))
              )}
            </div>
          </Popover.Content>
        </Popover.Portal>
      </Popover.Root>
    )
  }

  return (
    <div className="rounded-plate border-2 border-border-strong bg-bg-subtle p-4">
      <div className="mb-4 flex items-baseline justify-between gap-3">
        <h3 className="font-display text-sm font-bold uppercase tracking-[0.08em] text-fg">Mapa de posiciones</h3>
        <p className="font-mono text-xs font-bold text-fg-muted">
          {covered}/{POSITIONS.length} cubiertas
        </p>
      </div>

      {/* Vehicle outline, top-down. Decorative: the interactive nodes sit on top. */}
      <div className="relative mx-auto aspect-[4/5] w-full max-w-[19rem] sm:max-w-sm">
        <svg viewBox="0 0 200 250" className="absolute inset-0 h-full w-full" aria-hidden="true">
          <g fill="none" stroke="currentColor" className="text-border-strong" strokeWidth="2.5">
            <path d="M60 40 Q60 24 100 24 Q140 24 140 40 L146 96 Q150 125 146 154 L140 210 Q140 226 100 226 Q60 226 60 210 L54 154 Q50 125 54 96 Z" />
            <path d="M68 60 Q100 52 132 60 L136 88 Q100 82 64 88 Z" />
            <path d="M64 168 Q100 160 136 168 L132 196 Q100 190 68 196 Z" />
            <line x1="54" y1="120" x2="146" y2="120" strokeDasharray="4 6" />
          </g>
        </svg>

        {Object.entries(SPATIAL_NODES).map(([pos, node]) =>
          renderNode(pos, node.short, 'absolute -translate-x-1/2 -translate-y-1/2 whitespace-nowrap', {
            left: `${node.x}%`,
            top: `${node.y}%`,
          })
        )}
      </div>

      <div className="mt-4 border-t-2 border-border pt-3">
        <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.1em] text-fg-subtle">Sin ubicación en el vehículo</p>
        <div className="flex flex-wrap gap-2">
          {NON_SPATIAL.map((pos) => renderNode(pos, SHORT_LABELS[pos], ''))}
        </div>
      </div>
    </div>
  )
}
