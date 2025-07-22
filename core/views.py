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

            # 1️ Enviar Web Push
            titulo = f"Alerta AMBER: {alerta.nombre_desaparecido}"
            mensaje = f"Última ubicación: {alerta.ultima_ubicacion}. Reporta al 104"
            url = request.build_absolute_uri(reverse('detalle_alerta', args=[alerta.id]))
            try:
                send_web_push_notification(titulo, mensaje, url)
            except Exception as e:
                print("Error en Web Push:", e)

            # 2 Enviar SMS con Twilio
            try:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            except Exception as e:
                print("Error creando Twilio Client:", e)
            sms_mensaje = (
            f"🔴 Alerta AMBER: {alerta.nombre_desaparecido} desapareció en {alerta.ultima_ubicacion}. "
            f"Más info: {url} Llama al 104."
            )

            for usuario in UserSMS.objects.all():
                try:
                    client.messages.create(
                        body=sms_mensaje,
                        from_=settings.TWILIO_FROM_NUMBER,
                        to=usuario.telefono
                    )
                except Exception as e:
                    print(f"Error al enviar SMS a {usuario.telefono}: {e}")

            messages.success(request, "✅ Alerta creada. Notificaciones Web Push y SMS enviadas.")
            form = AlertaAmberForm()
        else:
            print(form.errors)
    else:
        form = AlertaAmberForm()

    alertas = AlertaAmber.objects.filter(activa=True)
    return render(request, 'core/admin/crear_alerta.html', {'form': form, 'alertas': alertas})

@staff_member_required
def sms_alert_view(request):
    if request.method == 'POST':
        if 'registrar' in request.POST:
            nombre = request.POST['nombre']
            telefono = "+507" + request.POST['telefono'].strip()

            if not UserSMS.objects.filter(telefono=telefono).exists():
                UserSMS.objects.create(nombre=nombre, telefono=telefono)
                messages.success(request, "Número registrado correctamente.")
            else:
                messages.info(request, "Este número ya está registrado.")

        elif 'enviar_sms' in request.POST:
            alerta = AlertaAmber.objects.filter(activa=True).last()
            if alerta:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                mensaje = f" Alerta AMBER: {alerta.nombre_desaparecido} desapareció en {alerta.ultima_ubicacion}. Reporta al 104."

                for user in UserSMS.objects.all():
                    try:
                        client.messages.create(
                            body=mensaje,
                            from_=settings.TWILIO_FROM_NUMBER,
                            to=user.telefono
                        )
                    except Exception as e:
                        print(f"Error con {user.telefono}: {e}")
                messages.success(request, "SMS enviados a todos los usuarios registrados.")
            else:
                messages.error(request, "No hay alertas activas para enviar.")

        return redirect('sms_alert')

    total = UserSMS.objects.count()
    return render(request, 'core/admin/sms_alert.html', {
        'total_registrados': total
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


#vista sms admin registro numero



#vista usuarios


def inicio(request):
    return render(request, 'core/publico/inicio.html')

def lista_alertas(request):
    alertas = AlertaAmber.objects.filter(activa=True).order_by('-fecha_creacion')
    return render(request, 'core/publico/lista_alertas.html', {'alertas': alertas})

