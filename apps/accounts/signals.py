import logging
from typing import Any

from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(user_login_failed)
def log_failed_sign_in(sender: Any, **kwargs: Any) -> None:
    """A security event (conventions/security.md §5): logging only, no business.

    The credentials are never logged: the username is personal data.
    """
    logger.warning(
        'Security event: %s', 'sign_in_failed', extra={'event': 'sign_in_failed'}
    )
