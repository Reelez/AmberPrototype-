self.addEventListener('install', function(event) {
  console.log('✔️ Service Worker instalado');
});

self.addEventListener('push', function(event) {
  console.log('💥 Push recibido:', event);
  console.log('🔗 URL recibida:', event.data.json().url);
  let data = {};
  if (event.data) {
    data = event.data.json();
  }
  const options = {
    body: data.body || 'Tienes una nueva alerta',
    data: { url: data.url }
  };
  event.waitUntil(
    self.registration.showNotification(data.title || 'Alerta AMBER', options)
  );
});


self.addEventListener('notificationclick', function(event) {
  console.log('🔔 Notificación clickeada', event.notification.data.url);
  event.notification.close();

  const urlToOpen = event.notification.data.url;

  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    }).then(function(clientList) {
      for (let i = 0; i < clientList.length; i++) {
        let client = clientList[i];
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        console.log('🌐 Abriendo nueva ventana:', urlToOpen);
        return clients.openWindow(urlToOpen);
      }
    })
  );
});


