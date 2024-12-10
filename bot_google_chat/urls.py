from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('aplications.guests.urls', 'guests'), namespace='guests')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
