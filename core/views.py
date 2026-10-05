from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.services.webpush_service import enviar_web_push
from .forms import AlertaAmberForm
from .models import AlertaAmber


def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            auth_login(request, user)
            return redirect('dashboard')
        elif user is not None:
            messages.error(request, 'Tu cuenta no tiene permisos para acceder al panel')
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

            # Enviar Web Push
            titulo = f"Alerta AMBER: {alerta.nombre_desaparecido}"
            mensaje = f"Última ubicación: {alerta.ultima_ubicacion}. Reporta al 104"
            enviar_web_push(titulo, mensaje, url)

            messages.success(request, "Alerta creada. El envío de notificaciones Web Push quedó en cola.")
            return redirect('crear_alerta')

    else:
        form = AlertaAmberForm()

    alertas = AlertaAmber.objects.filter(activa=True)
    return render(request, 'core/admin/crear_alerta.html', {
        'form': form,
        'alertas': alertas,
        'titulo': 'Crear Alerta Amber',
        'texto_boton': 'Enviar alerta',
    })


@staff_member_required
def editar_alerta(request, pk):
    """Edit an existing alert. Editing never triggers a new broadcast."""
    alerta = get_object_or_404(AlertaAmber, pk=pk)
    if request.method == 'POST':
        form = AlertaAmberForm(request.POST, request.FILES, instance=alerta)
        if form.is_valid():
            form.save()
            messages.success(request, "Alerta actualizada.")
            return redirect('detalle_alerta_admin', pk=alerta.pk)
    else:
        form = AlertaAmberForm(instance=alerta)

    return render(request, 'core/admin/crear_alerta.html', {
        'form': form,
        'alerta': alerta,
        'titulo': f'Editar Alerta Amber: {alerta.nombre_desaparecido}',
        'texto_boton': 'Guardar cambios',
        'editando': True,
    })


def detalle_alerta(request, pk):
    alerta = get_object_or_404(AlertaAmber, pk=pk)
    return render(request, 'core/detalle_alerta.html', {'alerta': alerta})

@staff_member_required
def detalle_alerta_admin(request, pk):
    alerta = get_object_or_404(AlertaAmber, pk=pk)
    return render(request, 'core/admin/detalle_alerta_admin.html', {'alerta': alerta})

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






#vista usuarios


def inicio(request):
    return render(request, 'core/publico/inicio.html')

def lista_alertas(request):
    alertas = AlertaAmber.objects.filter(activa=True).order_by('-fecha_creacion')
    return render(request, 'core/publico/lista_alertas.html', {'alertas': alertas})

