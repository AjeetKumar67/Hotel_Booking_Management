from django.apps import AppConfig


class HotelappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hotelapp'
    
    def ready(self):
        import hotelapp.signals
