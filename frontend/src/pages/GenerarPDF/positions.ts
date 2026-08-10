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

/**
 * Where each position sits around the vehicle, as percentages of the map box.
 * Only the six angular positions are placed on the body — the rest (documents,
 * driver, road kit, jack) are not spatial and would be a lie on a diagram.
 */
export const SPATIAL_NODES: Record<string, { x: number; y: number; short: string }> = {
  '2': { x: 50, y: 6, short: 'Frontal' },
  '3': { x: 82, y: 22, short: 'Frontal lat.' },
  '5': { x: 92, y: 50, short: 'Lado der.' },
  '7': { x: 82, y: 78, short: 'Lat. trasera' },
  '6': { x: 50, y: 94, short: 'Trasera' },
  '4': { x: 8, y: 50, short: 'Lado izq.' },
}

/** Positions with no meaningful place on the vehicle outline. */
export const NON_SPATIAL = ['1', '8', '9', '10', '11']

export const SHORT_LABELS: Record<string, string> = {
  '1': 'Formato',
  '8': 'Conductor',
  '9': 'Kit',
  '10': 'Gato y repuesto',
  '11': 'SOAT',
}
