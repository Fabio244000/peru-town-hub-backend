# Generic messages used by the exception handler for every module.
VALIDATION_ERROR_MESSAGE = 'Error de validación'
INTERNAL_SERVER_ERROR_MESSAGE = 'Error interno del servidor'
NOT_FOUND_MESSAGE = 'Recurso no encontrado'
RATE_LIMITED_MESSAGE = 'Hiciste muchas consultas. Espera un momento.'
# One single text for any credential failure (conventions/contracts.md §5).
UNAUTHENTICATED_MESSAGE = 'Inicia sesión para continuar.'

# Generic error codes (conventions/contracts.md §3).
VALIDATION_ERROR_CODE = 'validation_error'
NOT_FOUND_CODE = 'not_found'
RATE_LIMITED_CODE = 'rate_limited'
INTERNAL_ERROR_CODE = 'internal_error'

# Business days and hours are Peru's (conventions/contracts.md §3).
BUSINESS_TIME_ZONE = 'America/Lima'

# JWT claims checked on every token (conventions/security.md §1).
JWT_ISSUER = 'comunity-town-api'
JWT_AUDIENCE = 'comunity-town-api'
JWT_LEEWAY_SECONDS = 5

# Migration state the deploy records and restores (system output, in English).
MIGRATION_ZERO = 'zero'
MIGRATION_IRREVERSIBLE = 'Migration {migration} cannot be reversed: fix forward.'
MIGRATION_IRREVERSIBLE_CODE = 'migration_irreversible'
MIGRATION_REVERTED = '{app_label} {before} → {after}'
NO_MIGRATIONS_REVERTED = 'No migrations reverted'
# The deploy tells "fix forward" (this code) from "rollback failed" (any other).
MIGRATION_IRREVERSIBLE_EXIT_CODE = 3
MIGRATION_STATE_HELP = (
    'Registra el estado de las migraciones o vuelve a uno registrado (deploy)'
)
RECORD_HELP = 'Imprime el estado actual en una línea JSON'
RESTORE_HELP = 'Vuelve al estado registrado e imprime lo revertido'
STATE_HELP = 'El estado que imprimió record'
