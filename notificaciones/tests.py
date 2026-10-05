import json
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.urls import reverse
from pywebpush import WebPushException

from core.services.webpush_service import enviar_web_push

from .models import WebPushSubscription
from .utils import send_web_push_notification


def subscription_payload(endpoint='https://fcm.googleapis.com/fcm/send/abc', auth='authkey', p256dh='p256dhkey'):
    return {'endpoint': endpoint, 'keys': {'auth': auth, 'p256dh': p256dh}}


class PF5SaveSubscriptionTests(TestCase):
    """PF5: storing push subscriptions (RF4)."""

    def post(self, body):
        return self.client.post(
            reverse('save_subscription'),
            data=body if isinstance(body, str) else json.dumps(body),
            content_type='application/json',
        )

    def test_subscription_is_stored_with_endpoint_and_keys(self):
        """A valid subscription is persisted with its endpoint, auth and p256dh keys."""
        response = self.post(subscription_payload())
        self.assertEqual(response.status_code, 200)
        sub = WebPushSubscription.objects.get()
        self.assertEqual(sub.endpoint, 'https://fcm.googleapis.com/fcm/send/abc')
        self.assertEqual(sub.auth, 'authkey')
        self.assertEqual(sub.p256dh, 'p256dhkey')
        self.assertIsNotNone(sub.created_at)

    def test_same_endpoint_is_deduplicated_and_keys_updated(self):
        """Posting the same endpoint twice keeps a single row and refreshes its keys."""
        self.post(subscription_payload())
        self.post(subscription_payload(auth='newauth'))
        self.assertEqual(WebPushSubscription.objects.count(), 1)
        self.assertEqual(WebPushSubscription.objects.get().auth, 'newauth')

    def test_invalid_payloads_return_400(self):
        """Malformed JSON or missing fields are rejected with HTTP 400 and nothing is stored."""
        bodies = (
            'not json',
            {'endpoint': 'https://push.example/x'},
            {'keys': {}},
            [1, 2],
            {'endpoint': '', 'keys': {'auth': 'a', 'p256dh': 'p'}},
        )
        for body in bodies:
            with self.subTest(body=body):
                self.assertEqual(self.post(body).status_code, 400)
        self.assertEqual(WebPushSubscription.objects.count(), 0)

    def test_endpoints_outside_known_push_services_are_rejected(self):
        """Only HTTPS endpoints of real push services are accepted, preventing SSRF to internal hosts."""
        rejected = (
            'http://fcm.googleapis.com/fcm/send/abc',
            'https://169.254.169.254/latest/meta-data',
            'https://db:3306/',
            'https://evil.example/fcm.googleapis.com',
            'https://fcm.googleapis.com.evil.example/abc',
        )
        for endpoint in rejected:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.post(subscription_payload(endpoint=endpoint)).status_code, 400)
        accepted = (
            'https://updates.push.services.mozilla.com/wpush/v2/abc',
            'https://wns2-bl2p.notify.windows.com/w/?token=abc',
            'https://web.push.apple.com/abc',
        )
        for endpoint in accepted:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.post(subscription_payload(endpoint=endpoint)).status_code, 200)
        self.assertEqual(WebPushSubscription.objects.count(), len(accepted))

    def test_oversized_keys_are_rejected(self):
        """Keys longer than the 255-character columns return HTTP 400 instead of a server error."""
        self.assertEqual(self.post(subscription_payload(auth='a' * 256)).status_code, 400)
        self.assertEqual(self.post(subscription_payload(p256dh='p' * 256)).status_code, 400)
        self.assertEqual(WebPushSubscription.objects.count(), 0)

    def test_only_post_is_allowed(self):
        """GET requests to the subscription endpoint return HTTP 405."""
        self.assertEqual(self.client.get(reverse('save_subscription')).status_code, 405)


@override_settings(WEBPUSH_ASYNC=False)
class PF6BroadcastTests(TestCase):
    """PF6: broadcast to all subscribers (RF5)."""

    def test_broadcast_calls_webpush_once_per_subscription_with_json_payload(self):
        """Broadcasting to N subscriptions calls webpush N times with a JSON payload (title, body, url)."""
        for i in range(3):
            WebPushSubscription.objects.create(endpoint=f'https://push.example/{i}', auth='a', p256dh='p')
        with patch('notificaciones.utils.webpush') as mock_webpush:
            summary = enviar_web_push('Alerta AMBER: Test', 'Cuerpo', 'http://testserver/detalle_alerta/1/')
        self.assertEqual(mock_webpush.call_count, 3)
        self.assertEqual(summary, {'sent': 3, 'failed': 0, 'deleted': 0})
        endpoints = set()
        for call in mock_webpush.call_args_list:
            payload = json.loads(call.kwargs['data'])
            self.assertEqual(payload, {
                'title': 'Alerta AMBER: Test',
                'body': 'Cuerpo',
                'url': 'http://testserver/detalle_alerta/1/',
            })
            self.assertEqual(set(call.kwargs['subscription_info']), {'endpoint', 'keys'})
            endpoints.add(call.kwargs['subscription_info']['endpoint'])
        self.assertEqual(len(endpoints), 3)

    def test_broadcast_sets_24h_ttl_and_high_urgency(self):
        """Each push is sent with TTL=86400 s and Urgency: high (WNS/Edge rejects TTL=0)."""
        WebPushSubscription.objects.create(endpoint='https://wns2.notify.windows.com/w/?token=x', auth='a', p256dh='p')
        with patch('notificaciones.utils.webpush') as mock_webpush:
            enviar_web_push('Alerta AMBER: Test', 'Cuerpo', 'http://testserver/detalle_alerta/1/')
        kwargs = mock_webpush.call_args.kwargs
        self.assertEqual(kwargs['ttl'], 86400)
        self.assertEqual(kwargs['headers'], {'Urgency': 'high'})

    def test_broadcast_without_subscriptions_sends_nothing(self):
        """With no subscriptions the broadcast calls nothing and reports zero sent."""
        with patch('notificaciones.utils.webpush') as mock_webpush:
            summary = send_web_push_notification('t', 'b', 'http://x/')
        mock_webpush.assert_not_called()
        self.assertEqual(summary, {'sent': 0, 'failed': 0, 'deleted': 0})


class PF7ExpiredSubscriptionTests(TestCase):
    """PF7: purge of expired subscriptions (RF7)."""

    def push_with_status(self, status_code):
        WebPushSubscription.objects.create(endpoint='https://push.example/gone', auth='a', p256dh='p')
        error = WebPushException('push failed', response=Mock(status_code=status_code))
        with patch('notificaciones.utils.webpush', side_effect=error):
            return send_web_push_notification('t', 'b', 'http://x/')

    def test_410_response_deletes_subscription(self):
        """A 410 Gone response removes the subscription and counts it as deleted."""
        summary = self.push_with_status(410)
        self.assertEqual(WebPushSubscription.objects.count(), 0)
        self.assertEqual(summary, {'sent': 0, 'failed': 0, 'deleted': 1})

    def test_404_response_deletes_subscription(self):
        """A 404 Not Found response also removes the subscription."""
        summary = self.push_with_status(404)
        self.assertEqual(WebPushSubscription.objects.count(), 0)
        self.assertEqual(summary['deleted'], 1)

    def test_500_response_keeps_subscription(self):
        """A transient 500 error keeps the subscription and counts it as failed."""
        summary = self.push_with_status(500)
        self.assertEqual(WebPushSubscription.objects.count(), 1)
        self.assertEqual(summary, {'sent': 0, 'failed': 1, 'deleted': 0})

    def test_one_failure_does_not_stop_the_broadcast(self):
        """An expired subscription does not prevent delivery to the remaining subscribers."""
        WebPushSubscription.objects.create(endpoint='https://push.example/a-gone', auth='a', p256dh='p')
        WebPushSubscription.objects.create(endpoint='https://push.example/b-ok', auth='a', p256dh='p')
        gone = WebPushException('gone', response=Mock(status_code=410))

        def fake_webpush(subscription_info, **kwargs):
            if subscription_info['endpoint'].endswith('a-gone'):
                raise gone

        with patch('notificaciones.utils.webpush', side_effect=fake_webpush):
            summary = send_web_push_notification('t', 'b', 'http://x/')
        self.assertEqual(summary, {'sent': 1, 'failed': 0, 'deleted': 1})
        remaining = list(WebPushSubscription.objects.values_list('endpoint', flat=True))
        self.assertEqual(remaining, ['https://push.example/b-ok'])
