"""
URL configuration for inventory_project project.
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from inventory_app import views

urlpatterns = [
    # تسجيل الدخول والخروج - مخصص
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('', include('inventory_app.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

