"""Read-only public API: JSON endpoints and CAP v1.2 XML export (no DRF)."""
import mimetypes
import xml.etree.ElementTree as ET

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from .models import AlertaAmber

CAP_NAMESPACE = 'urn:oasis:names:tc:emergency:cap:1.2'
EMERGENCY_PHONE = '104'


def _iso(dt):
    """ISO 8601 timestamp with UTC offset, as required by CAP."""
    return timezone.localtime(dt).isoformat(timespec='seconds')


def _absolute(request, path):
    return request.build_absolute_uri(path)


def alerta_to_dict(alerta, request):
    return {
        'id': alerta.pk,
        'numero_reporte': alerta.numero_reporte,
        'nombre_desaparecido': alerta.nombre_desaparecido,
        'edad': alerta.edad,
        'genero': alerta.get_genero_display(),
        'activa': alerta.activa,
        'fecha_creacion': _iso(alerta.fecha_creacion),
        'ultima_ubicacion': alerta.ultima_ubicacion,
        'fecha_desaparicion': alerta.fecha_desaparicion.isoformat(),
        'hora_desaparicion': alerta.hora_desaparicion.isoformat(timespec='minutes'),
        'estatura_cm': alerta.estatura,
        'contextura': alerta.contextura,
        'tipo_cabello': alerta.tipo_cabello,
        'color_cabello': alerta.color_cabello,
        'color_ojos': alerta.color_ojos,
        'color_piel': alerta.color_piel,
        'señas_particulares': alerta.señas_particulares,
        'otros_detalles': alerta.otros_detalles,
        'imagen': _absolute(request, alerta.imagen.url) if alerta.imagen else None,
        'url': _absolute(request, reverse('detalle_alerta', args=[alerta.pk])),
        'cap': _absolute(request, reverse('api_alerta_cap', args=[alerta.pk])),
    }


@require_GET
def api_alertas(request):
    alertas = AlertaAmber.objects.filter(activa=True).order_by('-fecha_creacion')
    data = [alerta_to_dict(a, request) for a in alertas]
    return JsonResponse({'count': len(data), 'results': data}, json_dumps_params={'ensure_ascii': False})


@require_GET
def api_alerta_detalle(request, pk):
    alerta = get_object_or_404(AlertaAmber, pk=pk)
    return JsonResponse(alerta_to_dict(alerta, request), json_dumps_params={'ensure_ascii': False})


def build_cap_xml(alerta, request):
    """Return a CAP v1.2 <alert> document (bytes) for the given alert."""
    ET.register_namespace('', CAP_NAMESPACE)

    def tag(name):
        return f'{{{CAP_NAMESPACE}}}{name}'

    def add(parent, name, text):
        el = ET.SubElement(parent, tag(name))
        el.text = str(text)
        return el

    detail_url = _absolute(request, reverse('detalle_alerta', args=[alerta.pk]))

    root = ET.Element(tag('alert'))
    add(root, 'identifier', alerta.numero_reporte or f'AAPAN-{alerta.pk}')
    add(root, 'sender', settings.CAP_SENDER)
    add(root, 'sent', _iso(alerta.fecha_creacion))
    add(root, 'status', 'Actual')
    add(root, 'msgType', 'Alert' if alerta.activa else 'Cancel')
    add(root, 'scope', 'Public')

    info = ET.SubElement(root, tag('info'))
    add(info, 'language', 'es-PA')
    add(info, 'category', 'Rescue')
    add(info, 'event', 'Alerta AMBER')
    add(info, 'urgency', 'Immediate')
    # Fixed value: an AMBER alert is only activated when there is imminent
    # danger, so severity is never an operator choice.
    add(info, 'severity', 'Extreme')
    add(info, 'certainty', 'Observed')
    add(info, 'senderName', 'Alerta AMBER Panamá')
    add(info, 'headline', f'Alerta AMBER: {alerta.nombre_desaparecido}')

    description = (
        f'{alerta.nombre_desaparecido}, {alerta.edad} años, {alerta.get_genero_display().lower()}. '
        f'Visto por última vez en {alerta.ultima_ubicacion} el '
        f'{alerta.fecha_desaparicion.isoformat()} a las {alerta.hora_desaparicion.strftime("%H:%M")}. '
        f'Estatura {alerta.estatura} cm, contextura {alerta.contextura}, '
        f'cabello {alerta.tipo_cabello} {alerta.color_cabello}, ojos {alerta.color_ojos}, '
        f'piel {alerta.color_piel}.'
    )
    if alerta.señas_particulares:
        description += f' Señas particulares: {alerta.señas_particulares}.'
    if alerta.otros_detalles:
        description += f' {alerta.otros_detalles}'
    add(info, 'description', description)
    add(info, 'instruction', f'Si tiene información, llame al {EMERGENCY_PHONE}.')
    add(info, 'web', detail_url)
    add(info, 'contact', f'Policía Nacional de Panamá: {EMERGENCY_PHONE}')

    if alerta.imagen:
        resource = ET.SubElement(info, tag('resource'))
        add(resource, 'resourceDesc', f'Fotografía de {alerta.nombre_desaparecido}')
        mime, _ = mimetypes.guess_type(alerta.imagen.name)
        add(resource, 'mimeType', mime or 'image/jpeg')
        add(resource, 'uri', _absolute(request, alerta.imagen.url))

    area = ET.SubElement(info, tag('area'))
    add(area, 'areaDesc', alerta.ultima_ubicacion)

    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


@require_GET
def api_alerta_cap(request, pk):
    alerta = get_object_or_404(AlertaAmber, pk=pk)
    return HttpResponse(build_cap_xml(alerta, request), content_type='application/cap+xml; charset=utf-8')
