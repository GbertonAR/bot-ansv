// static/js/chat_init.js
(async function () {
  const userID = 'dl_' + Math.random().toString(36).substring(2, 9);

  // --------------- Sidebar (sin cambios) ---------------
  const sidebar = document.getElementById('sidebar');
  const openSidebarBtn = document.getElementById('openSidebarBtn');
  const closeSidebarBtn = document.getElementById('closeSidebarBtn');
  const overlay = document.createElement('div');
  overlay.className = 'overlay';
  document.body.appendChild(overlay);

  const openSidebar = () => {
    sidebar.classList.add('active');
    overlay.style.display = 'block';
    setTimeout(() => (overlay.style.backgroundColor = 'rgba(0,0,0,.5)'), 50);
  };
  const closeSidebar = () => {
    sidebar.classList.remove('active');
    overlay.style.backgroundColor = 'rgba(0,0,0,0)';
    setTimeout(() => (overlay.style.display = 'none'), 500);
  };
  openSidebarBtn.addEventListener('click', openSidebar);
  closeSidebarBtn.addEventListener('click', closeSidebar);
  overlay.addEventListener('click', closeSidebar);

  // --------------- Web Chat ---------------
  try {
    const res = await fetch('/chat-config');
    const cfg = await res.json();
    console.log('🟢 /chat-config →', cfg);

    const token = cfg.token;
    if (!token) {
      throw new Error('Token vacío o indefinido');
    }

    const directLine = window.WebChat.createDirectLine({ token });

    const store = window.WebChat.createStore(); // si querés interceptar acciones, lo haces luego

    const styleOptions = {
      bubbleBackground: 'rgba(0,0,255,.1)',
      bubbleFromUserBackground: 'rgba(0,255,0,.1)',
      botAvatarImage: '/static/ansv_avatar.png',
      userAvatarImage: '/static/user_avatar.png',
      botAvatarInitials: 'BS',
      userAvatarInitials: 'TU',
      avatarSize: 40,
      hideUploadButton: true
    };

    window.WebChat.renderWebChat(
      {
        directLine,
        store,
        locale: 'es-ES',
        userID,
        username: 'Usuario Web',
        styleOptions
      },
      document.getElementById('webchat')
    );

    console.log('✅ Web Chat conectado con token:', token.slice(0, 12), '...');
  } catch (err) {
    console.error('❌ Error iniciando Web Chat:', err);
    alert('No se pudo iniciar el chat. Revisa la consola para más detalles.');
  }
})();