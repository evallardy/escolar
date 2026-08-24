/**
 * Patrón AJAX del proyecto: navegación e interacción parcial sin recargar la
 * página completa, apoyándose en AjaxTemplateMixin del backend (que responde
 * con el fragmento cuando detecta el header X-Requested-With).
 *
 * Convenciones:
 *   - <a data-ajax-link data-target="#selector" href="...">           -> GET, reemplaza el contenedor
 *   - <form data-ajax-form data-target="#selector" method="post">...  -> envía el form, reemplaza el contenedor
 *   - <div data-ajax-poll="30000" data-target="#selector" data-url="..."> -> refresco periódico
 */
(function () {
  "use strict";

  const AJAX_HEADER = { "X-Requested-With": "XMLHttpRequest" };

  function getCookie(name) {
    const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return match ? decodeURIComponent(match[2]) : null;
  }

  const CSRF_TOKEN = getCookie("csrftoken");

  function reemplazarContenedor(selector, html) {
    const contenedor = document.querySelector(selector);
    if (contenedor) {
      contenedor.innerHTML = html;
    }
  }

  async function navegarAjax(url, targetSelector, pushState) {
    try {
      const resp = await fetch(url, { headers: AJAX_HEADER, credentials: "same-origin" });
      const html = await resp.text();
      reemplazarContenedor(targetSelector, html);
      if (pushState) {
        window.history.pushState({ ajaxUrl: url, target: targetSelector }, "", url);
      }
    } catch (err) {
      console.error("Error de navegación AJAX:", err);
      window.location.href = url; // Fallback: navegación normal.
    }
  }

  async function enviarFormAjax(form, targetSelector) {
    const method = (form.getAttribute("method") || "GET").toUpperCase();
    const url = form.getAttribute("action") || window.location.pathname;
    const formData = new FormData(form);

    const opciones = {
      method,
      headers: Object.assign({}, AJAX_HEADER, CSRF_TOKEN ? { "X-CSRFToken": CSRF_TOKEN } : {}),
      credentials: "same-origin",
    };

    if (method === "GET") {
      const params = new URLSearchParams(formData).toString();
      return navegarAjax(`${url}?${params}`, targetSelector, true);
    }

    opciones.body = formData;

    try {
      const resp = await fetch(url, opciones);
      const html = await resp.text();
      reemplazarContenedor(targetSelector, html);
    } catch (err) {
      console.error("Error al enviar formulario AJAX:", err);
      form.submit(); // Fallback: envío normal.
    }
  }

  document.addEventListener("click", function (evento) {
    const link = evento.target.closest("[data-ajax-link]");
    if (!link) return;
    evento.preventDefault();
    const target = link.getAttribute("data-target") || "#app-content";
    navegarAjax(link.getAttribute("href"), target, true);
  });

  document.addEventListener("submit", function (evento) {
    const form = evento.target.closest("[data-ajax-form]");
    if (!form) return;
    evento.preventDefault();
    const target = form.getAttribute("data-target") || "#app-content";
    enviarFormAjax(form, target);
  });

  // Navegación con los botones atrás/adelante del navegador.
  window.addEventListener("popstate", function (evento) {
    if (evento.state && evento.state.ajaxUrl) {
      navegarAjax(evento.state.ajaxUrl, evento.state.target, false);
    }
  });

  // Refresco periódico de paneles (ej. asistencia en vivo, ubicaciones GPS).
  document.querySelectorAll("[data-ajax-poll]").forEach(function (el) {
    const intervalo = parseInt(el.getAttribute("data-ajax-poll"), 10) || 30000;
    const url = el.getAttribute("data-url");
    const target = el.getAttribute("data-target") || `#${el.id}`;
    if (!url) return;
    setInterval(function () {
      navegarAjax(url, target, false);
    }, intervalo);
  });

  // Mostrar/ocultar el sidebar en pantallas pequeñas.
  document.addEventListener("click", function (evento) {
    if (evento.target.closest("#btn-toggle-sidebar")) {
      document.getElementById("sidebar")?.classList.toggle("show");
    }
  });
})();
