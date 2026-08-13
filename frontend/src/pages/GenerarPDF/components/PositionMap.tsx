import { useState, type CSSProperties } from 'react'
import * as Popover from '@radix-ui/react-popover'
import clsx from 'clsx'
import { POSITIONS, SPATIAL_NODES, NON_SPATIAL, SHORT_LABELS, MAP_VIEWBOX, SLOT_SIZE } from '../positions'
import type { ImageFile, Confidence } from '../useImageQueue'

type PositionMapProps = {
  images: ImageFile[]
  onAssign: (imageId: string, position: string) => void
}

type Tone = 'empty' | 'high' | 'medium' | 'neutral'

function toneOf(filled: ImageFile[]): Tone {
  if (filled.length === 0) return 'empty'
  const confidence: Confidence | undefined = filled[0].confidence
  if (confidence === 'high') return 'high'
  if (confidence === 'medium') return 'medium'
  return 'neutral'
}

// Line and slot border share one tone map, so the guide line always matches
// the state of the thing it points to — confidence when assigned, "empty"
// (dashed) when not. Confidence is only meaningful once a photo is in the
// slot, so it doubles as the fill signal.
const STROKE_TONE: Record<Tone, string> = {
  empty: 'text-border-strong',
  high: 'text-signal-500',
  medium: 'text-plate-500',
  neutral: 'text-fg-subtle',
}
const BORDER_TONE: Record<Tone, string> = {
  empty: 'border-dashed border-border-strong bg-bg-subtle',
  high: 'border-signal-500 bg-bg-subtle',
  medium: 'border-plate-500 bg-bg-subtle',
  neutral: 'border-border-strong bg-bg-subtle',
}

const SPATIAL_ORDER = Object.keys(SPATIAL_NODES).sort((a, b) => Number(a) - Number(b))

/**
 * Right-angle guide line from a body point to its photo slot, in the shared
 * MAP_VIEWBOX coordinate space: point → horizontal to the vertical channel →
 * vertical to the slot's height → horizontal to the slot's facing edge.
 * Front/rear positions have no channel and connect with one straight run.
 */
function guidePoints(pos: string): string {
  const node = SPATIAL_NODES[pos]
  const { x, y, slotX, slotY, channel } = node
  if (channel == null) {
    const edgeY = slotY < y ? slotY + SLOT_SIZE.height / 2 : slotY - SLOT_SIZE.height / 2
    return `${x},${y} ${slotX},${edgeY}`
  }
  const edgeX = slotX < x ? slotX + SLOT_SIZE.width / 2 : slotX - SLOT_SIZE.width / 2
  return `${x},${y} ${channel},${y} ${channel},${slotY} ${edgeX},${slotY}`
}

/**
 * The inspector physically walks around the vehicle, so the six angular
 * positions sit where they actually are, each linked to its photo by a
 * right-angle guide line — the same rotation-plan vocabulary as a dimensioned
 * technical drawing. Documents, driver and the road kit have no place on the
 * body: they get the same slot, unlined, in a row below.
 */
export default function PositionMap({ images, onAssign }: PositionMapProps) {
  const [open, setOpen] = useState<string | null>(null)

  const byPosition = (pos: string) => images.filter((img) => img.assignedPosition === pos)
  const unassigned = images.filter((img) => !img.assignedPosition)
  const covered = POSITIONS.filter((p) => byPosition(p.value).length > 0).length

  function renderSlot(pos: string, style: CSSProperties, className: string) {
    const def = POSITIONS.find((p) => p.value === pos)!
    const filled = byPosition(pos)
    const tone = toneOf(filled)
    const isOpen = open === pos
    const photo = filled[0]

    return (
      <Popover.Root key={pos} open={isOpen} onOpenChange={(next) => setOpen(next ? pos : null)}>
        <Popover.Trigger asChild>
          <button
            style={style}
            aria-label={`Posición ${pos}, ${def.label.replace(/^\d+\.\s*/, '')}, ${
              filled.length === 0 ? 'sin asignar' : `${filled.length} de ${def.max} asignada`
            }`}
            className={clsx(
              'relative overflow-hidden rounded-plate border-2 transition-colors duration-150',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-500 focus-visible:ring-offset-2 focus-visible:ring-offset-bg',
              BORDER_TONE[tone],
              className
            )}
          >
            {photo ? (
              <>
                <img src={photo.preview} alt="" className="absolute inset-0 h-full w-full object-cover" />
                <span className="absolute left-1 top-1 rounded-chip bg-black/60 px-1.5 py-0.5 font-mono text-[10px] font-bold text-white">
                  {pos.padStart(2, '0')}
                </span>
                {def.max > 1 && (
                  <span className="absolute right-1 top-1 rounded-chip bg-black/60 px-1.5 py-0.5 font-mono text-[10px] font-bold text-white">
                    {filled.length}/{def.max}
                  </span>
                )}
                <span className="absolute inset-x-0 bottom-0 truncate bg-black/60 px-1.5 py-0.5 text-center text-[9px] font-bold uppercase tracking-wide text-white">
                  {SHORT_LABELS[pos]}
                </span>
              </>
            ) : (
              <span className="flex h-full w-full flex-col items-center justify-center gap-0.5 px-1 text-center text-fg-subtle">
                <span className="font-mono text-xs font-bold">{pos.padStart(2, '0')}</span>
                <span className="text-[9px] font-bold uppercase tracking-wide">{SHORT_LABELS[pos]}</span>
              </span>
            )}
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
    <div className="rounded-plate border border-border-strong bg-bg-subtle p-4">
      <div className="mb-4 flex items-baseline justify-between gap-3">
        <h3 className="font-display text-sm font-bold uppercase tracking-[0.08em] text-fg">Mapa de posiciones</h3>
        <p className="font-mono text-xs font-bold text-fg-muted">
          {covered}/{POSITIONS.length} cubiertas
        </p>
      </div>

      {/* Vehicle outline with a right-angle guide line from each body point to
          its photo slot — a rotation plan, not decoration. The SVG only draws
          the body and the lines; the slots themselves are HTML buttons laid
          out in the same coordinate space so the lines always land exactly
          on their edges. */}
      <div className="relative mx-auto aspect-[3/4] w-full max-w-xs sm:max-w-sm">
        <svg
          viewBox={`0 0 ${MAP_VIEWBOX.width} ${MAP_VIEWBOX.height}`}
          className="absolute inset-0 h-full w-full"
          aria-hidden="true"
        >
          <g fill="none" stroke="currentColor" className="text-border-strong" strokeWidth="2.5" strokeLinejoin="round">
            {/* Straight sides (x=140/220 for y 120–360) so the six body
                points above land exactly on the outline, not near it. */}
            <path d="M160 100 L200 100 Q220 100 220 120 L220 360 Q220 380 200 380 L160 380 Q140 380 140 360 L140 120 Q140 100 160 100 Z" />
            <path d="M150 140 Q180 130 210 140" />
            <path d="M150 340 Q180 350 210 340" />
            <line x1="180" y1="120" x2="180" y2="360" strokeDasharray="3 7" strokeWidth="1.5" />
          </g>

          {SPATIAL_ORDER.map((pos) => {
            const filled = byPosition(pos)
            const tone = toneOf(filled)
            const node = SPATIAL_NODES[pos]
            return (
              <g key={pos} className={STROKE_TONE[tone]}>
                <polyline
                  points={guidePoints(pos)}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinejoin="miter"
                  strokeDasharray={tone === 'empty' ? '4 4' : undefined}
                />
                <circle cx={node.x} cy={node.y} r="3" fill="currentColor" />
              </g>
            )
          })}
        </svg>

        {SPATIAL_ORDER.map((pos) => {
          const node = SPATIAL_NODES[pos]
          return renderSlot(
            pos,
            {
              left: `${(node.slotX / MAP_VIEWBOX.width) * 100}%`,
              top: `${(node.slotY / MAP_VIEWBOX.height) * 100}%`,
              width: `${(SLOT_SIZE.width / MAP_VIEWBOX.width) * 100}%`,
              height: `${(SLOT_SIZE.height / MAP_VIEWBOX.height) * 100}%`,
            },
            'absolute -translate-x-1/2 -translate-y-1/2'
          )
        })}
      </div>

      <div className="mt-4 border-t border-border pt-3">
        <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.1em] text-fg-subtle">Sin ubicación en el vehículo</p>
        <div className="flex flex-wrap gap-2">
          {NON_SPATIAL.map((pos) => renderSlot(pos, {}, 'h-16 w-24 shrink-0'))}
        </div>
      </div>
    </div>
  )
}
