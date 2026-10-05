import io
import shutil
import tempfile
import xml.etree.ElementTree as ET
from datetime import date, time
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from notificaciones.models import WebPushSubscription

from .forms import AlertaAmberForm
from .models import AlertaAmber

CAP_NS = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
TEMP_MEDIA = tempfile.mkdtemp(prefix='amber-test-media-')


def make_image_file(name='foto.png'):
    buffer = io.BytesIO()
    Image.new('RGB', (20, 20), color='red').save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


def alert_form_data(**overrides):
    data = {
        'nombre_desaparecido': 'Maria Perez',
        'edad': 8,
        'genero': 'F',
        'ultima_ubicacion': 'Parque Omar, Ciudad de Panama',
        'fecha_desaparicion': date(2026, 1, 15).isoformat(),
        'hora_desaparicion': time(14, 30).strftime('%H:%M'),
        'estatura': 120,
        'contextura': 'Delgada',
        'tipo_cabello': 'Liso',
        'color_cabello': 'Negro',
        'color_ojos': 'Cafe',
        'color_piel': 'Trigueña',
        'señas_particulares': 'Lunar en la mejilla',
        'otros_detalles': 'Vestia uniforme escolar azul. ' * 5,
    }
    data.update(overrides)
    return data


def create_alert(**overrides):
    fields = {
        'nombre_desaparecido': 'Juan Gomez',
        'edad': 10,
        'genero': 'M',
        'ultima_ubicacion': 'San Miguelito',
        'fecha_desaparicion': date(2026, 2, 1),
        'hora_desaparicion': time(9, 0),
        'estatura': 130,
        'contextura': 'Media',
        'tipo_cabello': 'Rizado',
        'color_cabello': 'Castaño',
        'color_ojos': 'Negros',
        'color_piel': 'Morena',
        'imagen': 'alertas_imagenes/test.png',
    }
    fields.update(overrides)
    return AlertaAmber.objects.create(**fields)


@override_settings(MEDIA_ROOT=TEMP_MEDIA, WEBPUSH_ASYNC=False)
class AmberTestBase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pass1234', is_staff=True)
        self.regular = User.objects.create_user('regular', password='pass1234', is_staff=False)

    def login_staff(self):
        self.client.login(username='staff', password='pass1234')


class PF1LoginTests(AmberTestBase):
    """PF1: access control for the administrative panel (RF1)."""

    def test_staff_user_can_log_in_and_reach_dashboard(self):
        """A staff user submitting valid credentials is redirected to the dashboard and can open it."""
        response = self.client.post(reverse('login'), {'username': 'staff', 'password': 'pass1234'})
        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)

    def test_non_staff_user_is_rejected_with_error_message(self):
        """A valid non-staff user is not logged in and sees an error message on the login page."""
        response = self.client.post(reverse('login'), {'username': 'regular', 'password': 'pass1234'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'no tiene permisos')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_invalid_credentials_are_rejected(self):
        """Wrong credentials keep the user on the login page with an error message and no session."""
        response = self.client.post(reverse('login'), {'username': 'staff', 'password': 'wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Credenciales inválidas')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_admin_views_require_staff(self):
        """Anonymous and non-staff users are redirected away from every administrative view."""
        alerta = create_alert()
        urls = [
            reverse('dashboard'),
            reverse('crear_alerta'),
            reverse('lista_alertas_admin'),
            reverse('detalle_alerta_admin', args=[alerta.pk]),
            reverse('editar_alerta', args=[alerta.pk]),
        ]
        for url in urls:
            with self.subTest(url=url, user='anonymous'):
                self.assertEqual(self.client.get(url).status_code, 302)
        self.client.login(username='regular', password='pass1234')
        for url in urls:
            with self.subTest(url=url, user='non-staff'):
                self.assertEqual(self.client.get(url).status_code, 302)

    def test_change_state_requires_staff(self):
        """A non-staff POST to the state-change endpoint does not modify the alert."""
        alerta = create_alert()
        self.client.login(username='regular', password='pass1234')
        self.client.post(reverse('cambiar_estado_alerta', args=[alerta.pk]), {'accion': 'desactivar'})
        alerta.refresh_from_db()
        self.assertTrue(alerta.activa)


class PF2CreateAlertTests(AmberTestBase):
    """PF2: alert creation and broadcast (RF2, RF5)."""

    def test_create_alert_generates_report_number_and_broadcasts(self):
        """Creating an alert stores it with a generated numero_reporte and triggers one Web Push per subscription."""
        WebPushSubscription.objects.create(endpoint='https://push.example/1', auth='a', p256dh='p')
        self.login_staff()
        with patch('notificaciones.utils.webpush') as mock_webpush:
            response = self.client.post(
                reverse('crear_alerta'),
                {**alert_form_data(), 'imagen': make_image_file()},
            )
        self.assertRedirects(response, reverse('crear_alerta'))
        alerta = AlertaAmber.objects.get()
        self.assertTrue(alerta.activa)
        self.assertRegex(alerta.numero_reporte, rf'^AAPAN-{alerta.pk}-\d{{8}}$')
        self.assertEqual(mock_webpush.call_count, 1)

    def test_long_otros_detalles_is_accepted(self):
        """The otros_detalles field accepts text longer than the former 25-character limit."""
        self.login_staff()
        with patch('notificaciones.utils.webpush'):
            self.client.post(reverse('crear_alerta'), {**alert_form_data(), 'imagen': make_image_file()})
        self.assertGreater(len(AlertaAmber.objects.get().otros_detalles), 100)

    def test_invalid_form_does_not_create_or_broadcast(self):
        """A submission with missing required fields creates no alert and sends no push."""
        self.login_staff()
        with patch('notificaciones.utils.webpush') as mock_webpush:
            response = self.client.post(reverse('crear_alerta'), {'nombre_desaparecido': 'X'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AlertaAmber.objects.count(), 0)
        mock_webpush.assert_not_called()

    @override_settings(WEBPUSH_ASYNC=True)
    def test_broadcast_runs_in_a_daemon_thread_when_async(self):
        """With WEBPUSH_ASYNC enabled the dispatch is handed to a daemon thread instead of blocking the request."""
        from core.services.webpush_service import enviar_web_push
        with patch('core.services.webpush_service.threading.Thread') as mock_thread:
            enviar_web_push('t', 'b', 'http://x/')
        self.assertTrue(mock_thread.call_args.kwargs['daemon'])
        mock_thread.return_value.start.assert_called_once()


class PF3EditAndResolveTests(AmberTestBase):
    """PF3: editing and resolving alerts (RF2)."""

    def test_edit_alert_updates_fields_without_rebroadcast(self):
        """Editing an alert persists the new values and does not send any Web Push."""
        alerta = create_alert()
        WebPushSubscription.objects.create(endpoint='https://push.example/1', auth='a', p256dh='p')
        self.login_staff()
        with patch('notificaciones.utils.webpush') as mock_webpush:
            response = self.client.post(
                reverse('editar_alerta', args=[alerta.pk]),
                alert_form_data(nombre_desaparecido='Nombre Corregido'),
            )
        self.assertRedirects(response, reverse('detalle_alerta_admin', args=[alerta.pk]))
        alerta.refresh_from_db()
        self.assertEqual(alerta.nombre_desaparecido, 'Nombre Corregido')
        self.assertEqual(alerta.imagen.name, 'alertas_imagenes/test.png')
        mock_webpush.assert_not_called()

    def test_edit_form_is_prefilled(self):
        """The edit page renders the wizard pre-filled with the stored alert data."""
        alerta = create_alert()
        self.login_staff()
        response = self.client.get(reverse('editar_alerta', args=[alerta.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Juan Gomez"')
        self.assertContains(response, 'Guardar cambios')

    def test_edit_form_renders_iso_date_and_time(self):
        """Date and time are pre-filled in ISO format so the HTML date/time inputs show them."""
        alerta = create_alert()
        self.login_staff()
        response = self.client.get(reverse('editar_alerta', args=[alerta.pk]))
        self.assertContains(response, f'value="{alerta.fecha_desaparicion:%Y-%m-%d}"')
        self.assertContains(response, f'value="{alerta.hora_desaparicion:%H:%M}"')

    def test_mark_resolved_and_reactivate(self):
        """Marking an alert as found sets activa=False without a broadcast, and it can be reactivated."""
        alerta = create_alert()
        self.login_staff()
        with patch('notificaciones.utils.webpush') as mock_webpush:
            self.client.post(reverse('cambiar_estado_alerta', args=[alerta.pk]), {'accion': 'desactivar'})
            alerta.refresh_from_db()
            self.assertFalse(alerta.activa)
            self.client.post(reverse('cambiar_estado_alerta', args=[alerta.pk]), {'accion': 'activar'})
            alerta.refresh_from_db()
            self.assertTrue(alerta.activa)
        mock_webpush.assert_not_called()

    def test_resolve_message_is_shown_on_dashboard_and_not_later(self):
        """The 'marked as found' message appears on the dashboard right away and not on the next create-alert page."""
        alerta = create_alert()
        self.login_staff()
        response = self.client.post(
            reverse('cambiar_estado_alerta', args=[alerta.pk]), {'accion': 'desactivar'}, follow=True
        )
        self.assertContains(response, 'La alerta fue marcada como Encontrada.')
        response = self.client.get(reverse('crear_alerta'))
        self.assertNotContains(response, 'La alerta fue marcada como Encontrada.')


class PF4PublicPortalTests(AmberTestBase):
    """PF4: public portal accessible without authentication (RF3)."""

    def test_public_pages_are_accessible_without_login(self):
        """Home, alert list and alert detail return HTTP 200 for anonymous visitors."""
        alerta = create_alert()
        for url in (reverse('inicio'), reverse('lista_alertas'), reverse('detalle_alerta', args=[alerta.pk])):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_list_shows_only_active_alerts(self):
        """The public list contains active alerts and hides resolved ones."""
        create_alert(nombre_desaparecido='Activa Uno')
        resuelta = create_alert(nombre_desaparecido='Resuelta Dos')
        AlertaAmber.objects.filter(pk=resuelta.pk).update(activa=False)
        response = self.client.get(reverse('lista_alertas'))
        self.assertContains(response, 'Activa Uno')
        self.assertNotContains(response, 'Resuelta Dos')

    @override_settings(VAPID_PUBLIC_KEY='test-public-key')
    def test_layout_has_activation_button_and_vapid_key(self):
        """The public layout renders the 'Activar alertas' button and injects the VAPID public key."""
        response = self.client.get(reverse('inicio'))
        self.assertContains(response, 'id="activarNotificaciones"')
        self.assertContains(response, "const publicKey = 'test-public-key';")


class PF8ValidationAndContactTests(AmberTestBase):
    """PF8: input validation, emergency contact and CAP export (RF6, RNF3, RNF4)."""

    def test_invalid_image_is_rejected(self):
        """A non-image file uploaded as photo makes the form invalid with an explanatory error."""
        fake = SimpleUploadedFile('fake.png', b'not an image', content_type='image/png')
        form = AlertaAmberForm(alert_form_data(), {'imagen': fake})
        self.assertFalse(form.is_valid())
        self.assertIn('imagen', form.errors)

    def test_valid_image_is_rewound_after_verification(self):
        """A valid image stays readable after verification so it can be stored in full."""
        upload = make_image_file()
        size = upload.size
        form = AlertaAmberForm(alert_form_data(), {'imagen': upload})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(len(form.cleaned_data['imagen'].read()), size)

    def test_detail_page_has_emergency_tel_links(self):
        """The public detail page shows tel: links for 104 and 520-1000."""
        alerta = create_alert()
        response = self.client.get(reverse('detalle_alerta', args=[alerta.pk]))
        self.assertContains(response, 'href="tel:104"')
        self.assertContains(response, 'href="tel:5201000"')

    def test_list_cards_have_emergency_tel_links(self):
        """Every card of the public list shows the tel: links."""
        create_alert()
        response = self.client.get(reverse('lista_alertas'))
        self.assertContains(response, 'href="tel:104"')
        self.assertContains(response, 'href="tel:5201000"')

    def test_json_api_lists_only_active_alerts(self):
        """GET /api/alertas/ returns JSON with active alerts only and detail returns one alert."""
        activa = create_alert(nombre_desaparecido='Activa')
        resuelta = create_alert(nombre_desaparecido='Resuelta')
        AlertaAmber.objects.filter(pk=resuelta.pk).update(activa=False)
        data = self.client.get(reverse('api_alertas')).json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['nombre_desaparecido'], 'Activa')
        detail = self.client.get(reverse('api_alerta_detalle', args=[activa.pk])).json()
        self.assertEqual(detail['numero_reporte'], activa.numero_reporte)

    def test_cap_xml_is_valid_cap_1_2(self):
        """cap.xml parses as XML and carries the mandatory CAP v1.2 elements with expected values."""
        alerta = create_alert()
        response = self.client.get(reverse('api_alerta_cap', args=[alerta.pk]))
        self.assertEqual(response.status_code, 200)
        root = ET.fromstring(response.content)
        self.assertEqual(root.tag, '{urn:oasis:names:tc:emergency:cap:1.2}alert')

        def text(path):
            return root.find(path, CAP_NS).text

        self.assertEqual(text('cap:identifier'), alerta.numero_reporte)
        self.assertTrue(text('cap:sender'))
        self.assertRegex(text('cap:sent'), r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$')
        self.assertEqual(text('cap:status'), 'Actual')
        self.assertEqual(text('cap:msgType'), 'Alert')
        self.assertEqual(text('cap:scope'), 'Public')
        self.assertEqual(text('cap:info/cap:language'), 'es-PA')
        self.assertEqual(text('cap:info/cap:category'), 'Rescue')
        self.assertEqual(text('cap:info/cap:event'), 'Alerta AMBER')
        self.assertEqual(text('cap:info/cap:urgency'), 'Immediate')
        self.assertEqual(text('cap:info/cap:severity'), 'Extreme')
        self.assertEqual(text('cap:info/cap:certainty'), 'Observed')
        self.assertIn('104', text('cap:info/cap:instruction'))
        self.assertTrue(text('cap:info/cap:web').endswith(reverse('detalle_alerta', args=[alerta.pk])))
        self.assertEqual(text('cap:info/cap:area/cap:areaDesc'), 'San Miguelito')
        self.assertTrue(text('cap:info/cap:resource/cap:uri').endswith('test.png'))

    def test_cap_xml_of_resolved_alert_is_cancel(self):
        """A resolved alert is exported with msgType Cancel."""
        alerta = create_alert()
        AlertaAmber.objects.filter(pk=alerta.pk).update(activa=False)
        root = ET.fromstring(self.client.get(reverse('api_alerta_cap', args=[alerta.pk])).content)
        self.assertEqual(root.find('cap:msgType', CAP_NS).text, 'Cancel')
