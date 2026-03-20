from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import AlertaAmberForm
from .models import AlertaAmber, UserSMS
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from notificaciones.utils import send_web_push_notification
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import JsonResponse
from twilio.rest import Client
from core.services.webpush_service import enviar_web_push
from core.services.sms_service import enviar_sms
from .services.recaptcha_service import verificar_recaptcha



def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')  # Cambia al nombre de la vista que quieras
        else:
            messages.error(request, 'Credenciales inválidas')
    
    return render(request, 'core/login/login.html')

@staff_member_required
def dashboard(request):
    alertas = AlertaAmber.objects.filter(activa=True)
    return render(request, 'core/admin/dashboard.html', {'alertas': alertas})


@staff_member_required
def crear_alerta(request):
    if request.method == 'POST':
        form = AlertaAmberForm(request.POST, request.FILES)
        if form.is_valid():
            alerta = form.save()

            # URL de detalle de la alerta
            url = request.build_absolute_uri(reverse('detalle_alerta', args=[alerta.id]))

            # 1️ Enviar Web Push
            titulo = f"Alerta AMBER: {alerta.nombre_desaparecido}"
            mensaje = f"Última ubicación: {alerta.ultima_ubicacion}. Reporta al 104"
            enviar_web_push(titulo, mensaje, url)

            # 2 Enviar SMS 
            enviar_sms(alerta, url)

            messages.success(request, "Alerta creada. Notificaciones enviadas (Web Push y SMS).")
            return redirect('crear_alerta')
               
    else:
        form = AlertaAmberForm()

    alertas = AlertaAmber.objects.filter(activa=True)
    return render(request, 'core/admin/crear_alerta.html', {'form': form, 'alertas': alertas})


#vista sms admin registro numero
def sms_alert_view(request):
    if request.method == 'POST':
        # Verificar reCAPTCHA
        if not verificar_recaptcha(request.POST.get('g-recaptcha-response')):
            messages.error(request, "Error de verificación reCAPTCHA.")
            return redirect('sms_alert')

        if request.POST.get('accion') == 'registrar':
            nombre = request.POST.get('nombre', '').strip()
            telefono_input = request.POST.get('telefono', '').strip()
            acepta = request.POST.get('acepta_alertas')

            if not acepta:
                messages.error(request, "Debes aceptar recibir alertas SMS.")
                return redirect('sms_alert')

            if not telefono_input or not nombre:
                messages.error(request, "Faltan datos obligatorios.")
                return redirect('sms_alert')

            # Limpiar número: quitar espacios, guiones, etc. y anteponer +507
            telefono_limpio = ''.join(filter(str.isdigit, telefono_input))
            telefono = "+507" + telefono_limpio

            if UserSMS.objects.filter(telefono=telefono).exists():
                messages.info(request, f"El número {telefono} ya está registrado.")
            else:
                UserSMS.objects.create(nombre=nombre, telefono=telefono)
                messages.success(request, "Número registrado correctamente.")

        elif 'enviar_sms' in request.POST:
            alerta = AlertaAmber.objects.filter(activa=True).last()
            if alerta:
                url = request.build_absolute_uri(reverse('detalle_alerta', args=[alerta.id]))
                enviar_sms(alerta, url)
                messages.success(request, "SMS enviados a todos los usuarios registrados.")
            else:
                messages.error(request, "No hay alertas activas para enviar.")

        return redirect('sms_alert')

    total = UserSMS.objects.count()
    return render(request, 'core/publico/sms_alert.html', {
        'total_registrados': total,
        'RECAPTCHA_SITE_KEY': settings.RECAPTCHA_SITE_KEY
    })



def detalle_alerta(request, pk):
    alerta = get_object_or_404(AlertaAmber, pk=pk)
    return render(request, 'core/detalle_alerta.html', {'alerta': alerta})

@staff_member_required
def lista_alertas_admin(request):
    alertas = AlertaAmber.objects.all()
    total_alertas = alertas.count()
    alertas_resueltas = alertas.filter(activa=False).count()
    alertas_activas = alertas.filter(activa=True)

    return render(request, 'core/admin/lista_alertas_admin.html', {
        'alertas': alertas,
        'total_alertas': total_alertas,
        'alertas_resueltas': alertas_resueltas,
        'alertas_activas': alertas_activas
    })

@staff_member_required
def lista_usuarios_sms(request):
    usuarios = UserSMS.objects.all().order_by('-registrado_en')
    return render(request, 'core/admin/lista_usuarios_sms.html', {'usuarios': usuarios})

@staff_member_required
def eliminar_usuario_sms(request, pk):
    usuario = get_object_or_404(UserSMS, pk=pk)
    usuario.delete()
    messages.success(request, f"El usuario {usuario.nombre} ha sido eliminado.")
    return redirect('sms')


@staff_member_required
def cambiar_estado_alerta(request, pk):
    alerta = get_object_or_404(AlertaAmber, pk=pk)

    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'desactivar':
            alerta.activa = False
            messages.success(request, "La alerta fue marcada como Encontrada.")
        elif accion == 'activar':
            alerta.activa = True
            messages.success(request, "La alerta fue reactivada.")
        alerta.save()

    return redirect('dashboard')






#vista usuarios


def inicio(request):
    return render(request, 'core/publico/inicio.html')

def lista_alertas(request):
    alertas = AlertaAmber.objects.filter(activa=True).order_by('-fecha_creacion')
    return render(request, 'core/publico/lista_alertas.html', {'alertas': alertas})

