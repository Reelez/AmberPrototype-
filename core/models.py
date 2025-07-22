from django.db import models
from django.contrib.auth.models import User
from datetime import time

class AlertaAmber(models.Model):
    
    #info principal
   
    nombre_desaparecido = models.CharField(max_length=100)  # Nombre del niño o persona desaparecida
    edad = models.PositiveIntegerField()
    genero = models.CharField(max_length=20, choices=[('M','Masculino'), ('F','Femenino')])
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    #ultima vez visto
    ultima_ubicacion = models.CharField(max_length=255)
    fecha_desaparicion = models.DateField() 
    hora_desaparicion = models.TimeField()

    #numero de reporte
    numero_reporte = models.CharField(max_length=50, blank=True, editable=False)
    imagen = models.ImageField(upload_to='alertas_imagenes/')  # Foto
   
    #Características físicas detalladas
    estatura = models.CharField(max_length=50)  
    contextura = models.CharField(max_length=50) 
    tipo_cabello = models.CharField(max_length=50)  
    color_cabello = models.CharField(max_length=50)  
    color_ojos = models.CharField(max_length=50)  
    color_piel = models.CharField(max_length=50)  
    #rasgos particulares
    señas_particulares = models.CharField(max_length=255, blank=True)
    #detalles extras
    otros_detalles = models.CharField(max_length=25, blank=True)

    activa = models.BooleanField(default=True, editable=False)
  # Si la alerta sigue activa

    def save(self, *args, **kwargs):
        creating = self.pk is None  # Detectamos si es nuevo
        super().save(*args, **kwargs)  # Guardamos primero para que tenga ID y fecha
        if creating and not self.numero_reporte:
            fecha_str = self.fecha_creacion.strftime('%Y%m%d')  # Fecha como 20250617
            self.numero_reporte = f"AAPAN-{self.id}-{fecha_str}"
            # Guardamos de nuevo para actualizar el número de reporte
            super().save(update_fields=['numero_reporte'])

    def __str__(self):
        return f"Alerta: {self.titulo} - {self.nombre_desaparecido}"


class UserSMS(models.Model):
    nombre =models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, unique=True)
    registrado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.telefono})"