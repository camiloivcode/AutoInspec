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
 * Where each position sits around the vehicle, as percentages of the map box.
 * Only the six angular positions are placed on the body — the rest (documents,
 * driver, road kit, jack) are not spatial and would be a lie on a diagram.
 * Coordinates are kept inset from the 0/100 edges so a marker centered on
 * them never clips the box.
 */
export const SPATIAL_NODES: Record<string, { x: number; y: number }> = {
  '2': { x: 50, y: 10 },
  '3': { x: 76, y: 24 },
  '5': { x: 86, y: 50 },
  '7': { x: 76, y: 76 },
  '6': { x: 50, y: 90 },
  '4': { x: 14, y: 50 },
}

/** Positions with no meaningful place on the vehicle outline. */
export const NON_SPATIAL = ['1', '8', '9', '10', '11']
