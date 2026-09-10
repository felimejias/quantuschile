(function () {
  function cleanRut(value) {
    return String(value || "").replace(/\./g, "").replace(/-/g, "").trim().toUpperCase();
  }

  function validateRut(value, required) {
    const clean = cleanRut(value);
    if (!clean) return !required;
    if (!/^\d{7,8}[0-9K]$/.test(clean)) return false;

    const body = clean.slice(0, -1);
    const dv = clean.slice(-1);
    let sum = 0;
    let multiplier = 2;

    for (let i = body.length - 1; i >= 0; i -= 1) {
      sum += Number(body[i]) * multiplier;
      multiplier = multiplier === 7 ? 2 : multiplier + 1;
    }

    const rest = 11 - (sum % 11);
    const expected = rest === 11 ? "0" : rest === 10 ? "K" : String(rest);
    return dv === expected;
  }

  function formatRut(value) {
    const clean = cleanRut(value);
    if (!clean) return "";
    let body = clean.slice(0, -1);
    const dv = clean.slice(-1);
    const groups = [];
    while (body.length > 0) {
      groups.unshift(body.slice(-3));
      body = body.slice(0, -3);
    }
    return `${groups.join(".")}-${dv}`;
  }

  function setState(input) {
    const required = input.hasAttribute("required") || input.dataset.rutRequired === "true";
    const ok = validateRut(input.value, required);
    input.classList.toggle("rut-invalid", !ok);
    input.classList.toggle("rut-valid", ok && cleanRut(input.value).length > 0);
    input.setCustomValidity(ok ? "" : "RUT inválido. Revisa el dígito verificador.");
    const help = input.parentElement && input.parentElement.querySelector("[data-rut-message]");
    if (help) {
      help.textContent = ok ? "" : "RUT inválido. Revisa el dígito verificador.";
    }
    return ok;
  }

  function attach(input) {
    input.addEventListener("blur", function () {
      if (input.value.trim()) input.value = formatRut(input.value);
      setState(input);
    });
    input.addEventListener("input", function () {
      input.setCustomValidity("");
      input.classList.remove("rut-invalid", "rut-valid");
      const help = input.parentElement && input.parentElement.querySelector("[data-rut-message]");
      if (help) help.textContent = "";
    });
  }

  window.QuantusRut = { cleanRut, validateRut, formatRut };

  document.addEventListener("DOMContentLoaded", function () {
    const inputs = Array.from(document.querySelectorAll("[data-rut]"));
    inputs.forEach(attach);
    document.querySelectorAll("form").forEach(function (form) {
      form.addEventListener("submit", function (event) {
        const scoped = Array.from(form.querySelectorAll("[data-rut]"));
        const firstInvalid = scoped.find((input) => !setState(input));
        if (firstInvalid) {
          event.preventDefault();
          firstInvalid.focus();
        }
      });
    });
  });
})();
