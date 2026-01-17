import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class CustomPasswordValidator:
    """
    Custom password validator that enforces strong password requirements.
    """

    def validate(self, password, user=None):
        errors = []

        # Check minimum length
        if len(password) < 8:
            errors.append(_("Пароль должен содержать минимум 8 символов."))

        # Check if password contains only digits
        if password.isdigit():
            errors.append(_("Пароль не может состоять только из цифр."))

        # Check if password contains only letters
        if password.isalpha():
            errors.append(_("Пароль должен содержать хотя бы одну цифру."))

        # Check for at least one uppercase letter
        if not re.search(r"[A-Z]", password):
            errors.append(
                _("Пароль должен содержать хотя бы одну заглавную букву.")
            )

        # Check for at least one lowercase letter
        if not re.search(r"[a-z]", password):
            errors.append(
                _("Пароль должен содержать хотя бы одну строчную букву.")
            )

        # Check for at least one digit
        if not re.search(r"\d", password):
            errors.append(_("Пароль должен содержать хотя бы одну цифру."))

        # Check for special characters (optional but recommended)
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append(
                _("Пароль должен содержать хотя бы один специальный символ.")
            )

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Пароль должен содержать минимум 8 символов, "
            "включая заглавные и строчные буквы, "
            "цифры и специальные символы."
        )
