from django.apps import AppConfig


class ComplainappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ComplainApp'
    def ready(self):
        import ComplainApp.signals
