from django.apps import AppConfig


class CapyShellConfig(AppConfig):
    name = "capy_shell"
    label = "capy_shell"
    verbose_name = "Capy Shell"
    # Set here, not left to the project, so the module's migrations are the
    # same in every project whatever its DEFAULT_AUTO_FIELD.
    default_auto_field = "django.db.models.BigAutoField"
