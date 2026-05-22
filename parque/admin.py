from django.contrib import admin

from .models import Equipo, TicketSoporte


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'marca', 'modelo', 'serie', 'razon_social_cliente', 'ciudad')
    list_filter = ('tipo', 'marca', 'ciudad', 'empresa_atencion')
    search_fields = ('marca', 'modelo', 'serie', 'razon_social_cliente')
    readonly_fields = ('public_id', 'qr_code', 'creado_en', 'actualizado_en')


@admin.register(TicketSoporte)
class TicketSoporteAdmin(admin.ModelAdmin):
    list_display = ('id', 'equipo', 'nombre_cliente', 'telefono', 'empresa', 'estado', 'creado_en')
    list_filter = ('estado', 'equipo__tipo', 'creado_en')
    search_fields = ('nombre_cliente', 'telefono', 'empresa', 'problema', 'equipo__serie')

# Register your models here.
