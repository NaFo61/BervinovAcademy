from django.apps import AppConfig
from django.forms.widgets import ClearableFileInput, TextInput
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        import users.signals  # noqa

        # Патчим виджет при загрузке приложения
        _original_clearable_render = ClearableFileInput.render

        def _patched_clearable_render(
            self, name, value, attrs=None, renderer=None
        ):
            html = _original_clearable_render(
                self, name, value, attrs, renderer
            )
            if not isinstance(html, str):
                html = (
                    html.decode("utf-8")
                    if hasattr(html, "decode")
                    else str(html)
                )

            replacements = {
                "Current:": _("Current:"),
                "Change:": _("Change:"),
                "Clear": _("Clear"),
                "Choose file to upload": _("Choose file to upload"),
                "Select value": _("Select value"),  # 🆕 Добавлено!
            }

            for k, v in replacements.items():
                try:
                    html = html.replace(k, str(v))
                except Exception:
                    pass

            return html

        ClearableFileInput.render = _patched_clearable_render

        # --- Перевод placeholder "Search apps and models..." ---
        _original_textinput_render = TextInput.render

        def _patched_textinput_render(
            self, name, value, attrs=None, renderer=None
        ):
            html = _original_textinput_render(
                self, name, value, attrs, renderer
            )
            if not isinstance(html, str):
                try:
                    html = html.decode("utf-8")
                except Exception:
                    html = str(html)

            try:
                html = html.replace(
                    "Search apps and models...",
                    str(_("Search apps and models...")),
                )
                html = html.replace(
                    "Type to search",
                    str(_("Type to search")),
                )
            except Exception:
                pass

            return html

        TextInput.render = _patched_textinput_render

        # --- Перевод кнопки "Filters" ---
        _original_render = TemplateResponse.render

        def _patched_render(self):
            html = _original_render(self)
            if hasattr(self, "content") and isinstance(
                self.content, (bytes, str)
            ):
                content = (
                    self.content.decode("utf-8")
                    if isinstance(self.content, bytes)
                    else self.content
                )
                content = content.replace("Filters", str(_("Filters")))
                content = content.replace(
                    "Reset filters", str(_("Reset filters"))
                )
                content = content.replace(
                    "No results found", str(_("No results found"))
                )
                content = content.replace(
                    "This page yielded into no results. "
                    "Create a new item or reset your filters.",
                    str(
                        _(
                            "This page yielded into no results. "
                            "Create a new item or reset your filters."
                        )
                    ),
                )
                self.content = content.encode("utf-8")
            return html

        TemplateResponse.render = _patched_render
