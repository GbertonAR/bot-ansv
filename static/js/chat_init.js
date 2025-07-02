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

  // ✅ Agrega acciones si es del bot
  if (!esUsuario) {
    const acciones = document.createElement("div");
    acciones.className = "acciones-respuesta";

    acciones.innerHTML = `
      <button class="accion" title="Me gusta" onclick="registrarReaccion(this, 'like')">
        <span style="color:green">👍</span>
      </button>
      <button class="accion" title="No me gusta" onclick="registrarReaccion(this, 'dislike')">
        <span style="color:red">👎</span>
      </button>
      <button class="accion" title="Copiar respuesta" onclick="copiarTexto(this)">
        📄
      </button>
      <button class="accion" title="Leer en voz alta" onclick="leerTexto(this)">
        🔈
      </button>
    `;

    mensaje.appendChild(acciones); // lo agregamos al bloque del mensaje completo
  }

  scrollAlFinal();
}

async function enviarMensaje() {
  const texto = input.value.trim();
  if (!texto) return;

  crearMensaje(texto, true);
  historial.push({ role: 'user', content: texto });
  input.value = '';

  if (texto.toLowerCase() === 'menu') {
      mostrarMenuOpciones();
      historial.push({ role: 'user', content: texto });
      input.value = '';
      return;
}


  // Muestra indicador de escritura
  const typing = document.createElement("div");
  typing.id = "typing-indicator";
  typing.className = "mensaje bot";
  // typing.innerHTML = `<div class="texto typing-dots">Escribiendo...</div>`;
  typing.innerHTML = `
  <div class="texto typing-dots">
    Escribiendo<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
  </div>`;
  chatBox.appendChild(typing);
  chatBox.scrollTop = chatBox.scrollHeight;


  try {
    const response = await fetch('/api/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: texto }) 
    });

    // Borra el indicador de "Escribiendo..."
    const indicador = document.getElementById("typing-indicator");
    if (indicador) indicador.remove();    

    const data = await response.json();
    const respuesta = data.reply || '[Sin respuesta]';
    historial.push({ role: 'assistant', content: respuesta });
    crearMensaje(respuesta, false);
  } catch (err) {
    crearMensaje('⚠️ Error de conexión', false);
  }
}


function mostrarMenuOpciones() {
  const mensaje = document.createElement('div');
  mensaje.className = 'mensaje bot';

  const avatar = document.createElement('img');
  avatar.src = '/static/ansv_avatar.png';
  avatar.className = 'avatar';

  const opciones = document.createElement('div');
  opciones.className = 'menu-opciones';

  const botones = [
    { icono: "📚", texto: "Información ANSV", valor: "informacion" },
    { icono: "📝", texto: "Soporte y Tickets", valor: "tickets" },
    { icono: "📄", texto: "Documentos", valor: "documentos" },
    { icono: "✍️", texto: "Formularios", valor: "formularios" },
    { icono: "📧", texto: "Contacto", valor: "contacto" }
  ];

  botones.forEach(btn => {
    const boton = document.createElement('button');
    boton.className = 'menu-boton';
    boton.innerHTML = `${btn.icono} ${btn.texto}`;
    boton.addEventListener('click', () => {
      input.value = btn.valor;
      enviarMensaje(); // simula envío del mensaje
    });
    opciones.appendChild(boton);
  });

  mensaje.appendChild(avatar);
  mensaje.appendChild(opciones);
  chatBox.appendChild(mensaje);
  scrollAlFinal();
}

enviarBtn.addEventListener('click', enviarMensaje);
input.addEventListener('keydown', e => {
  if (e.key === 'Enter') enviarMensaje();
});

document.getElementById('openSidebarBtn').addEventListener('click', () => {
  document.getElementById('sidebar').classList.add('active');
});


document.getElementById("editProfileBtn").addEventListener("click", () => {
  window.location.href = "/login"; 
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

function leerTexto(boton) {
  const texto = boton.closest(".mensaje").querySelector(".texto").innerText;
  const speech = new SpeechSynthesisUtterance(texto);
  speech.lang = "es-AR";
  window.speechSynthesis.speak(speech);
}

function copiarTexto(boton) {
  const texto = boton.closest(".mensaje").querySelector(".texto").innerText;
  navigator.clipboard.writeText(texto).then(() => {
    boton.innerText = "✅";
    setTimeout(() => boton.innerText = "📄", 1500);
  });
}

function registrarReaccion(boton, tipo) {
  boton.disabled = true;
  boton.style.opacity = 0.5;
  console.log("Reacción registrada:", tipo);
}
