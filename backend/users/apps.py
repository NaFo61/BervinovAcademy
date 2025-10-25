from django.apps import AppConfig
from django.forms.widgets import ClearableFileInput, TextInput
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        # Патчим виджет при загрузке приложения
        _original_clearable_render = ClearableFileInput.render

        def _patched_clearable_render(
            self, name, value, attrs=None, renderer=None
        ):
            html = _original_clearable_render(
                self, name, value, attrs, renderer
            )
            if not isinstance(html, str):
                try:
                    html = html.decode("utf-8")
                except Exception:
                    html = str(html)

            current_input_text = getattr(self, "input_text", None)
            if current_input_text:
                try:
                    repl = str(_(current_input_text))
                    html = html.replace(current_input_text, repl)
                except Exception:
                    pass

            try:
                html = html.replace("Current:", str(_("Current:")))
                html = html.replace("Change:", str(_("Change:")))
                html = html.replace("Clear", str(_("Clear")))
                html = html.replace(
                    "Choose file to upload", str(_("Choose file to upload"))
                )
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
                self.content = content.encode("utf-8")
            return html

        TemplateResponse.render = _patched_render
