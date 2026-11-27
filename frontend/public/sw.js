self.addEventListener('push', event => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (_) {}
  const title = data.title || 'Respectful Meet';
  event.waitUntil(self.registration.showNotification(title, {
    body: data.body || '',
    icon: '/logo-icon.png',
    badge: '/logo-icon.png',
    data: { url: data.url || '/notifications' },
    tag: data.tag || 'respectful-meet'
  }));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = event.notification.data?.url || '/notifications';
  event.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(list => {
    const existing = list.find(c => 'focus' in c);
    return existing ? existing.focus().then(() => existing.navigate(url)) : clients.openWindow(url);
  }));
});
