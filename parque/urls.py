from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='parque/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('panel/', views.dashboard, name='dashboard'),
    path('panel/equipos/', views.equipo_list, name='equipo_list'),
    path('panel/equipos/nuevo/', views.equipo_create, name='equipo_create'),
    path('panel/equipos/<int:pk>/', views.equipo_detail, name='equipo_detail'),
    path('panel/equipos/<int:pk>/editar/', views.equipo_update, name='equipo_update'),
    path('panel/equipos/<int:pk>/qr/', views.equipo_qr_download, name='equipo_qr_download'),
    path('panel/equipos/<int:pk>/eliminar/', views.equipo_delete, name='equipo_delete'),
    path('panel/tickets/', views.ticket_list, name='ticket_list'),
    path('panel/tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('panel/tickets/<int:pk>/eliminar/', views.ticket_delete, name='ticket_delete'),
    path('reportar/<uuid:public_id>/', views.public_report, name='public_report'),
    path('reportar/<uuid:public_id>/exito/', views.public_report_success, name='public_report_success'),
]
