// static/js/lanzador.js
window.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch("/api/mi-perfil");
    if (!res.ok) return;

    const data = await res.json();
    document.getElementById("conexion-status").style.display = "block";
  } catch (err) {
    console.warn("No autenticado");
  }
});
