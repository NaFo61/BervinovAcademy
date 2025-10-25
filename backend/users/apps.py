from django.apps import AppConfig
from django.forms.widgets import ClearableFileInput
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
