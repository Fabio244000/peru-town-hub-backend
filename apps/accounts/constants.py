from pathlib import Path

from django.db import models

# Formats (conventions/data.md §3; ticket xa367ije83, L1-L4).
PERSON_NAME_LENGTH = (2, 250)
PERSON_NAME_PATTERN = r"^[a-záéíóúñü']+([ -][a-záéíóúñü']+)*$"
USERNAME_LENGTH = (8, 30)
USERNAME_PATTERN = r'^[a-z]{3}[a-z0-9]{5,27}$'
USERNAME_LEADING_LETTERS = 3
USERNAME_ACCENTED_LETTERS = 'ñáéíóúüÑÁÉÍÓÚÜ'
PASSWORD_LENGTH = (8, 50)
PASSWORD_MAX_REPEATED = 3
# R4: the password differs from the username and each name in more than 4 characters.
PASSWORD_MIN_DIFFERENCE = 5
PHONE_MAX_LENGTH = 16
# Spanish names of the regions with their own numbering (Unicode CLDR).
COUNTRY_NAMES_PATH = Path(__file__).resolve().parent / 'data' / 'countries.yaml'


class PhoneStatus(models.TextChoices):
    UNVERIFIED = 'unverified', 'Por verificar'
    VERIFIED = 'verified', 'Verificado'


# Field labels (admin).
UUID_LABEL = 'identificador público'
PHONE_LABEL = 'celular'
PHONE_STATUS_LABEL = 'estado del celular'
POLICIES_ACCEPTED_AT_LABEL = 'aceptó las políticas'

# EN1: names.
FIRST_NAMES_REQUIRED = 'Escribe tus nombres.'
LAST_NAMES_REQUIRED = 'Escribe tus apellidos.'
NAME_TOO_SHORT = f'Escribe al menos {PERSON_NAME_LENGTH[0]} letras.'
NAME_INVALID_CHARACTERS = 'Usa solo letras, espacios, guiones y apóstrofos.'
NAME_TOO_LONG = '¡Quedó un poco largo! Intenta acortarlo.'

# EN2: username.
USERNAME_REQUIRED = 'Escribe un nombre de usuario.'
USERNAME_HAS_SPACES = 'Quita los espacios.'
USERNAME_HAS_ACCENTS = 'Sin ñ ni tildes.'
USERNAME_INVALID_CHARACTERS = 'Usa solo letras minúsculas y números.'
USERNAME_LEADING_LETTERS_MISSING = (
    f'Las {USERNAME_LEADING_LETTERS} primeras deben ser letras.'
)
USERNAME_TOO_SHORT = 'Te faltan {missing} caracteres.'
USERNAME_TOO_LONG = f'Usa como máximo {USERNAME_LENGTH[1]} caracteres.'

# EN3: username taken.
USERNAME_TAKEN = 'Ese nombre de usuario ya existe. Prueba con otro.'
USERNAME_TAKEN_CODE = 'username_taken'

# EN4: password.
PASSWORD_REQUIRED = 'Crea una contraseña.'
PASSWORD_LENGTH_INVALID = (
    f'Usa entre {PASSWORD_LENGTH[0]} y {PASSWORD_LENGTH[1]} caracteres.'
)
PASSWORD_MISSING_DIGIT = 'Agrega al menos un número.'
PASSWORD_MISSING_SPECIAL = 'Agrega al menos un carácter especial, como # o !.'
PASSWORD_WITH_SPACES = 'Quita los espacios.'
PASSWORD_REPEATED_CHARACTER = (
    f'No repitas un carácter más de {PASSWORD_MAX_REPEATED} veces seguidas.'
)

# EN5: password close to the username or a name.
PASSWORD_SIMILAR = 'No uses tu nombre ni tu usuario en la contraseña.'

# EN6: cellphone.
PHONE_REQUIRED = 'Escribe tu número de celular.'
PHONE_DIGITS_ONLY = 'Escribe solo los números de tu celular.'
PHONE_COUNTRY_INVALID = 'Elige el código de país de tu celular.'
PHONE_INVALID = 'Revisa tu número: en {country} tiene {digits} dígitos{prefix}.'
PHONE_INVALID_PREFIX = ' y empieza con {digit}'

# EN7: cellphone taken.
PHONE_TAKEN = 'Este celular ya tiene una cuenta.'
PHONE_TAKEN_CODE = 'phone_taken'

# R6: the policies are accepted by signing up.
POLICIES_NOT_ACCEPTED = (
    'Acepta los términos de uso y la política de privacidad para crear tu cuenta.'
)

# EN8, EN9: sign-up limits per device (R8, L6).
SIGNUP_HOURLY_LIMIT_REACHED = (
    'Desde este dispositivo se pidieron muchos registros. Inténtalo de nuevo en una '
    'hora. ¿Necesitas ayuda? Escríbenos a {support_email}'
)
SIGNUP_MONTHLY_LIMIT_REACHED = (
    'Desde este dispositivo se pidieron muchos registros. Inténtalo de nuevo el '
    'próximo mes. ¿Necesitas ayuda? Escríbenos a {support_email}'
)

# R7: the session.
TOKEN_TYPE = 'Bearer'
