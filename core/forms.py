from django import forms
from .models import AlertaAmber

class AlertaAmberForm(forms.ModelForm):
    

    class Meta:
        model = AlertaAmber
        fields = '__all__'
        widgets = {
            'fecha_desaparicion': forms.DateInput(attrs={'type': 'date'}),
            'hora_desaparicion': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }
        labels = {
            'estatura': 'Estatura (cm)',
        }
