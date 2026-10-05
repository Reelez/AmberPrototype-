from django import forms
from .models import AlertaAmber
from django.utils.html import strip_tags
from PIL import Image
from django.core.exceptions import ValidationError

class AlertaAmberForm(forms.ModelForm):
    class Meta:
        model = AlertaAmber
        exclude = ['numero_reporte', 'activa']
        widgets = {
            # HTML date/time inputs only accept ISO values, regardless of LANGUAGE_CODE.
            'fecha_desaparicion': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'hora_desaparicion': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control-file'}),
            'otros_detalles': forms.Textarea(attrs={'rows': 4}),
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

    def clean(self):
        cleaned_data = super().clean()
        # Sanitizar automáticamente todos los campos tipo texto
        for field_name, value in cleaned_data.items():
            if isinstance(value, str):
                cleaned_data[field_name] = strip_tags(value).strip()
        return cleaned_data

    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        # Only validate fresh uploads; an unchanged image on edit is already stored.
        if imagen and hasattr(imagen, 'content_type'):
            try:
                img = Image.open(imagen)
                img.verify()  # Verifica que sea una imagen válida
            except Exception:
                raise ValidationError("El archivo subido no es una imagen válida.")
            finally:
                imagen.seek(0)  # verify() consumes the stream; rewind before saving
        return imagen