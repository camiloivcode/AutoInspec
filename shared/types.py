"""
Tipos compartidos entre Backend, Frontend y Bot.
Mantiene consistencia en la nomenclatura de la API.
"""

# Estados de inspección
INSPECTION_STATUS_DRAFT = "draft"
INSPECTION_STATUS_IN_PROGRESS = "in_progress"
INSPECTION_STATUS_COMPLETED = "completed"
INSPECTION_STATUS_CANCELLED = "cancelled"

# Tipos de documento
DOCUMENT_TYPE_WORD = "word"
DOCUMENT_TYPE_PDF = "pdf"

# Estados de documento
DOCUMENT_STATUS_PENDING = "pending"
DOCUMENT_STATUS_GENERATED = "generated"
DOCUMENT_STATUS_ERROR = "error"

# Roles de usuario
USER_ROLE_ADMIN = "admin"
USER_ROLE_INSPECTOR = "inspector"
USER_ROLE_CLIENT = "client"

# Categorías de items de inspección
ITEM_CATEGORIES = [
    "motor",
    "transmisión",
    "frenos",
    "suspensión",
    "dirección",
    "eléctrico",
    "carrocería",
    "neumáticos",
    "iluminación",
    "escape",
    "refrigeración",
    "seguridad",
]
