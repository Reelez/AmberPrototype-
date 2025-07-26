from django import forms
from .models import AlertaAmber

class AlertaAmberForm(forms.ModelForm):

    class Meta:
        model = AlertaAmber
        exclude = ['numero_reporte', 'activa']
        widgets = {
            'fecha_desaparicion': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_desaparicion': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control-file'}),
        }
        labels = {
            'nombre_desaparecido': 'Nombre completo',
            'edad': 'Edad (años)',
            'genero': 'Género',
            'ultima_ubicacion': 'Última ubicación conocida',
            'fecha_desaparicion': 'Fecha de desaparición',
            'hora_desaparicion': 'Hora de desaparición',
            'imagen': 'Fotografía',
            'estatura': 'Estatura (cm)',
            'contextura': 'Contextura física',
            'tipo_cabello': 'Tipo de cabello',
            'color_cabello': 'Color de cabello',
            'color_ojos': 'Color de ojos',
            'color_piel': 'Color de piel',
            'señas_particulares': 'Señas particulares (si aplica)',
            'otros_detalles': 'Otros detalles',
        }

