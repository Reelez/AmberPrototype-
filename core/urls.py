from django.urls import path, re_path
from . import views
from django.views.static import serve
from django.conf import settings

# Vistas admin
admin_patterns = [
    path('crear-alerta/', views.crear_alerta, name='crear_alerta'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin/alertas/', views.lista_alertas_admin, name='lista_alertas_admin'),
    path('cambiar-estado-alerta/<int:pk>/', views.cambiar_estado_alerta, name='cambiar_estado_alerta'),
    path('sms-alert/', views.sms_alert_view, name='sms_alert'),
]

# Vistas públicas
public_patterns = [
    path('inicio/', views.inicio, name='inicio'),
    path('lista_alertas/', views.lista_alertas, name='lista_alertas'),
]

urlpatterns = [
    path('', views.custom_login, name='login'),
    path('detalle_alerta/<int:pk>/', views.detalle_alerta, name='detalle_alerta'),
    *admin_patterns,
    *public_patterns,
    re_path(r'^service-worker.js$', serve, {
        'document_root': settings.BASE_DIR / 'static',
        'path': 'service-worker.js',
    }),
]
