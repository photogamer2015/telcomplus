from django import forms

from .models import Equipo, TicketSoporte


class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = [
            'tipo',
            'marca',
            'modelo',
            'serie',
            'empresa_atencion',
            'razon_social_cliente',
            'provincia',
            'ciudad',
            'direccion',
            'area_departamento',
            'ubicacion_coordenadas',
        ]
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }


class ReportePublicoForm(forms.ModelForm):
    class Meta:
        model = TicketSoporte
        fields = ['nombre_cliente', 'telefono', 'empresa', 'problema']
        widgets = {
            'problema': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Describa el problema que presenta el equipo'}),
        }


class EstadoTicketForm(forms.ModelForm):
    class Meta:
        model = TicketSoporte
        fields = ['estado']
