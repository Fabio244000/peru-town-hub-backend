from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _


class AccountUserManager(UserManager):
    @classmethod
    def normalize_email(cls, email: str | None) -> str | None:
        # Django turns a missing email into '', which would break its uniqueness.
        return (email or '').strip().lower() or None


class User(AbstractUser):
    email = models.EmailField(_('email address'), null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = AccountUserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['email'], name='accounts_user_email_unique'
            ),
            models.CheckConstraint(
                condition=models.Q(email=Lower('email')),
                name='accounts_user_email_lowercase',
            ),
        ]
