// chat_init.js actualizado
const chatBox = document.getElementById('chat-box');
const input = document.getElementById('mensaje-input');
const enviarBtn = document.getElementById('enviar-btn');

let historial = [];

function scrollAlFinal() {
  chatBox.scrollTop = chatBox.scrollHeight;
}

function crearMensaje(texto, esUsuario = false) {
  const mensaje = document.createElement('div');
  mensaje.className = 'mensaje' + (esUsuario ? ' user' : '');

  const avatar = document.createElement('img');
  avatar.src = esUsuario ? '/static/user_avatar.png' : '/static/ansv_avatar.png';
  avatar.className = 'avatar';

  const textoDiv = document.createElement('div');
  textoDiv.className = 'texto';
  textoDiv.innerHTML = marked.parse(texto); // permitir texto enriquecido (negrita, etc.)

  mensaje.appendChild(avatar);
  mensaje.appendChild(textoDiv);
  chatBox.appendChild(mensaje);
  scrollAlFinal();
}

async function enviarMensaje() {
  const texto = input.value.trim();
  if (!texto) return;

  crearMensaje(texto, true);
  historial.push({ role: 'user', content: texto });
  input.value = '';

  try {
    const response = await fetch('/api/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: texto }) 
    });

    const data = await response.json();
    const respuesta = data.reply || '[Sin respuesta]';
    historial.push({ role: 'assistant', content: respuesta });
    crearMensaje(respuesta, false);
  } catch (err) {
    crearMensaje('⚠️ Error de conexión', false);
  }
}

enviarBtn.addEventListener('click', enviarMensaje);
input.addEventListener('keydown', e => {
  if (e.key === 'Enter') enviarMensaje();
});

document.getElementById('openSidebarBtn').addEventListener('click', () => {
  document.getElementById('sidebar').classList.add('active');
});




// ✅ Mostrar mensaje de bienvenida automáticamente al cargar
window.addEventListener('DOMContentLoaded', () => {
  const bienvenida = "👋 ¡Hola! Soy el asistente virtual de la ANSV.<br>Estoy aquí para ayudarte con información sobre seguridad vial, normativas, trámites y más.<br>Por favor, escribí tu consulta y te responderé lo antes posible.<br><br>🚦 <i>Trabajamos juntos por una movilidad más segura.</i>";
  crearMensaje(bienvenida, false);
});

document.getElementById('openSidebarBtn').addEventListener('click', function () {
  const sidebar = document.querySelector('.sidebar');
  sidebar.classList.toggle('show');
});