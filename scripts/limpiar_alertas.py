import os
from core.models import AlertaAmber
from django.conf import settings

def run():
    alertas = AlertaAmber.objects.all()
    total = alertas.count()

    for alerta in alertas:
        if alerta.imagen:
            ruta_imagen = alerta.imagen.path
            if os.path.exists(ruta_imagen):
                os.remove(ruta_imagen)
                print(f"Imagen eliminada: {ruta_imagen}")
            else:
                print(f"Imagen no encontrada: {ruta_imagen}")
        alerta.delete()

    print(f"{total} registros eliminados de AlertaAmber con sus imágenes.")
