// Mirrors INSPECTION_POSITIONS in backend/src/infrastructure/analysis/photo_classifier.py — keep both in sync.
export const POSITIONS = [
  { value: '1', label: '1. Formato de inspección', max: 1 },
  { value: '2', label: '2. Frontal', max: 1 },
  { value: '3', label: '3. Frontal lateral', max: 1 },
  { value: '4', label: '4. Lado izquierdo', max: 1 },
  { value: '5', label: '5. Lado derecho', max: 1 },
  { value: '6', label: '6. Trasera', max: 1 },
  { value: '7', label: '7. Lateral trasera', max: 1 },
  { value: '8', label: '8. Conductor', max: 1 },
  { value: '9', label: '9. Kit de carretera', max: 1 },
  { value: '10', label: '10. Gato y llanta de repuesto', max: 2 },
  { value: '11', label: '11. SOAT y documentos', max: 1 },
]

/** Short label for every position — used by the compact Select trigger and the map legend. */
export const SHORT_LABELS: Record<string, string> = {
  '1': 'Formato',
  '2': 'Frontal',
  '3': 'Frontal lat.',
  '4': 'Lado izq.',
  '5': 'Lado der.',
  '6': 'Trasera',
  '7': 'Lat. trasera',
  '8': 'Conductor',
  '9': 'Kit',
  '10': 'Gato y repuesto',
  '11': 'SOAT',
}

/**
 * Single coordinate system shared by the vehicle SVG and the HTML photo
 * slots layered on top of it, so a line drawn from a body point to a slot
 * never needs separate math in JS — both read from the same numbers.
 */
export const MAP_VIEWBOX = { width: 360, height: 480 }
export const SLOT_SIZE = { width: 100, height: 75 } // 4:3, matches PhotoCard's aspect ratio

/**
 * Where each of the six angular positions sits on the vehicle body (x, y),
 * where its photo slot sits (slotX, slotY), and — for the side positions —
 * the x of the vertical channel the guide line runs through on its way to
 * the slot. Front/rear positions connect with a single straight vertical
 * segment and don't need a channel.
 *
 * Body points sit exactly on the vehicle outline drawn in PositionMap.tsx
 * (straight sides at x=140/220 for y in [120,360], straight top/bottom at
 * y=100/380) — this is what lets the line touch the silhouette instead of
 * floating near it. If the outline ever changes, these have to move with it.
 *
 * Two rules if these ever move: a position's point and its slot must stay on
 * the same side of the body (nothing should have to cross the vehicle), and
 * each side's two channels must stay apart (120/130, 230/240) so their
 * vertical runs don't overlap.
 */
export const SPATIAL_NODES: Record<
  string,
  { x: number; y: number; slotX: number; slotY: number; channel?: number }
> = {
  '2': { x: 180, y: 100, slotX: 180, slotY: 47 },
  '3': { x: 140, y: 160, slotX: 60, slotY: 175, channel: 130 },
  '4': { x: 140, y: 270, slotX: 60, slotY: 305, channel: 120 },
  '5': { x: 220, y: 190, slotX: 300, slotY: 175, channel: 230 },
  '7': { x: 220, y: 300, slotX: 300, slotY: 305, channel: 240 },
  '6': { x: 180, y: 380, slotX: 180, slotY: 433 },
}

/** Positions with no meaningful place on the vehicle outline. */
export const NON_SPATIAL = ['1', '8', '9', '10', '11']
