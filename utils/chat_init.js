let escribiendoActivo = false;

// Agrega un mensaje al chat
function agregarMensaje(role, contenido) {
    const chatBox = document.getElementById("chat-box");
    const mensaje = document.createElement("div");
    mensaje.classList.add("mensaje", role);

    const avatar = document.createElement("img");
    avatar.classList.add("avatar");
    avatar.src = role === "user" ? "/static/user_avatar.png" : "/static/ansv_avatar.png";

    const texto = document.createElement("div");
    texto.classList.add("texto");
    texto.textContent = contenido;

    mensaje.appendChild(avatar);
    mensaje.appendChild(texto);
    chatBox.appendChild(mensaje);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Indicador visual de escritura del bot
function mostrarIndicadorEscribiendo() {
    if (escribiendoActivo) return;
    escribiendoActivo = true;

    const chatBox = document.getElementById("chat-box");
    const escribiendo = document.createElement("div");
    escribiendo.id = "indicador-escribiendo";
    escribiendo.classList.add("mensaje", "bot");
    escribiendo.innerHTML = `
        <img class="avatar" src="/static/ansv_avatar.png" />
        <div class="texto typing-dots">El asistente está escribiendo...</div>`;
    chatBox.appendChild(escribiendo);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function ocultarIndicadorEscribiendo() {
    const e = document.getElementById("indicador-escribiendo");
    if (e) e.remove();
    escribiendoActivo = false;
}

// Enviar mensaje al presionar el botón
document.getElementById("enviar-btn").addEventListener("click", enviarMensaje);

// Enviar mensaje con Enter
document.getElementById("mensaje-input").addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
        e.preventDefault();
        enviarMensaje();
    }
});

async function enviarMensaje() {
    const input = document.getElementById("mensaje-input");
    const mensaje = input.value.trim();
    if (!mensaje || escribiendoActivo) return;

    agregarMensaje("user", mensaje);
    input.value = "";

    mostrarIndicadorEscribiendo();

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user: "Invitado", message: mensaje }),
        });

        const data = await res.json();
        ocultarIndicadorEscribiendo();

        if (data.reply) {
            agregarMensaje("bot", data.reply);
            hablar(data.reply);
        } else {
            agregarMensaje("bot", "⚠️ Error del bot");
        }
    } catch (e) {
        ocultarIndicadorEscribiendo();
        agregarMensaje("bot", "⚠️ Error del bot");
        console.error("Error al enviar mensaje:", e);
    }
}

// Síntesis de voz
function hablar(texto) {
    const utterance = new SpeechSynthesisUtterance(texto);
    utterance.lang = "es-AR";
    window.speechSynthesis.speak(utterance);
}
