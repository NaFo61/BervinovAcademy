import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class CustomPasswordValidator:

    def validate(self, password, user=None):
        errors = []

        if len(password) < 8:
            errors.append(_("Пароль должен содержать минимум 8 символов."))

        if password.isdigit():
            errors.append(_("Пароль не может состоять только из цифр."))

        if password.isalpha():
            errors.append(_("Пароль должен содержать хотя бы одну цифру."))

        if not re.search(r"[A-Z]", password):
            errors.append(
                _("Пароль должен содержать хотя бы одну заглавную букву.")
            )

        if not re.search(r"[a-z]", password):
            errors.append(
                _("Пароль должен содержать хотя бы одну строчную букву.")
            )
        if not re.search(r"\d", password):
            errors.append(_("Пароль должен содержать хотя бы одну цифру."))

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
