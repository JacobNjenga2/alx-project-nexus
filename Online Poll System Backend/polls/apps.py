from django.apps import AppConfig


class PollsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'polls'
    verbose_name = 'Online Poll System'
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            import polls.signals  # noqa F401
        except ImportError:
            pass
