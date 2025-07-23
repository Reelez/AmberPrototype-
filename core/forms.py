from django import forms
from .models import AlertaAmber

class AlertaAmberForm(forms.ModelForm):
    

        class Meta:
            model = AlertaAmber
            exclude = ['numero_reporte', 'activa']  # Campos no editables
            widgets = {
                'fecha_desaparicion': forms.DateInput(attrs={'type': 'date'}),
                'hora_desaparicion': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            }
            labels = {
                'estatura': 'Estatura (cm)',
    }

