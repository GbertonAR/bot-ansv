// static/js/chat_init.js

(async function () {
    // Genera un ID de usuario aleatorio para cada sesión
    const userID = 'dl_' + Math.random().toString(36).substring(2, 9);

    // --- Lógica para abrir/cerrar el Sidebar ---
    const sidebar = document.getElementById('sidebar');
    const openSidebarBtn = document.getElementById('openSidebarBtn');
    const closeSidebarBtn = document.getElementById('closeSidebarBtn');

    // Crear el elemento overlay (backdrop)
    const overlay = document.createElement('div');
    overlay.className = 'overlay';
    document.body.appendChild(overlay);

    function openSidebar() {
        sidebar.classList.add('active');
        overlay.style.display = 'block'; // Mostrar el overlay
        setTimeout(() => overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)', 50); // Animación del overlay
    }

    function closeSidebar() {
        sidebar.classList.remove('active');
        overlay.style.backgroundColor = 'rgba(0, 0, 0, 0)'; // Animación de ocultar el overlay
        setTimeout(() => overlay.style.display = 'none', 500); // Ocultar el overlay después de la transición
    }

    openSidebarBtn.addEventListener('click', openSidebar);
    closeSidebarBtn.addEventListener('click', closeSidebar);
    overlay.addEventListener('click', closeSidebar); // Cerrar sidebar al hacer clic en el overlay

    // --- Configuración e Inicialización del Web Chat ---

    // Fetch del token desde tu bot local
    try {
        const res = await fetch('/chat-config'); // Ruta relativa a tu servidor
        const config = await res.json();
        const token = config.token;

        if (!token) {
            console.error("Error: Token de Direct Line no obtenido. Verifica la configuración de tu bot.");
            alert("Error al cargar el chat: Token de autenticación no disponible.");
            return; // Detiene la ejecución si no hay token
        }

        const store = window.WebChat.createStore();

        // Opciones de estilo personalizadas, incluyendo los avatares
        const styleOptions = {
            bubbleBackground: 'rgba(0, 0, 255, .1)',
            bubbleFromUserBackground: 'rgba(0, 255, 0, .1)',
            
            // === AVATARES ===
            botAvatarImage: '/static/ansv_avatar.png',   // CORREGIDO: Añadido /static/
            userAvatarImage: '/static/user_avatar.png',   // CORREGIDO: Añadido /static/
            botAvatarInitials: 'BS', // Iniciales del Bot
            userAvatarInitials: 'TU', // Iniciales del Usuario

            avatarSize: 40,
            hideUploadButton: true,
            sendBoxBackground: '#f5f5f5',
            sendBoxBorderRadius: 20,
            sendBoxButtonColor: '#6a0dad',
            sendBoxButtonHoverColor: '#5a099a',
            microphoneButtonColor: '#6a0dad',
            microphoneButtonHoverColor: '#5a099a',
            focusBorderColor: '#6a0dad',
            accent: '#6a0dad',
            bubbleBorderRadius: 10,
            bubbleFromUserBorderRadius: 10,
            groupTimestamp: 5000
        };

        window.WebChat.renderWebChat({
            directLine: window.WebChat.createDirectLine({
                 token,
            }),
           
            userID: userID,
            username: 'Usuario Web',
            locale: 'es-ES',
            store: store,
            styleOptions: styleOptions
        }, document.getElementById('webchat'));

        console.log("Web Chat y Sidebar inicializados.");

    } catch (error) {
        console.error("Error al inicializar Web Chat o obtener token:", error);
        alert("No se pudo iniciar el chat. Por favor, revisa la consola para más detalles.");
    }

})();