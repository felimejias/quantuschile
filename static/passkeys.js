(function () {
  function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.content;
    const input = document.querySelector('input[name="_csrf_token"]');
    return input ? input.value : "";
  }

  function b64urlToBuffer(value) {
    const base64 = value.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - value.length % 4) % 4);
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    return bytes.buffer;
  }

  function bufferToB64url(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = "";
    bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
    return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
  }

  function prepareCreationOptions(options) {
    options.challenge = b64urlToBuffer(options.challenge);
    options.user.id = b64urlToBuffer(options.user.id);
    if (Array.isArray(options.excludeCredentials)) {
      options.excludeCredentials = options.excludeCredentials.map((item) => ({ ...item, id: b64urlToBuffer(item.id) }));
    }
    return options;
  }

  function prepareRequestOptions(options) {
    options.challenge = b64urlToBuffer(options.challenge);
    if (Array.isArray(options.allowCredentials)) {
      options.allowCredentials = options.allowCredentials.map((item) => ({ ...item, id: b64urlToBuffer(item.id) }));
    }
    return options;
  }

  function credentialToJSON(credential) {
    const response = credential.response;
    const json = {
      id: credential.id,
      rawId: bufferToB64url(credential.rawId),
      type: credential.type,
      response: {},
      clientExtensionResults: credential.getClientExtensionResults ? credential.getClientExtensionResults() : {},
      authenticatorAttachment: credential.authenticatorAttachment || undefined,
    };
    ["clientDataJSON", "attestationObject", "authenticatorData", "signature", "userHandle"].forEach((key) => {
      if (response[key]) json.response[key] = bufferToB64url(response[key]);
    });
    return json;
  }

  async function getJSON(url) {
    const response = await fetch(url, { credentials: "same-origin" });
    const data = await response.json();
    if (!response.ok || data.ok === false) throw new Error(data.error || "No fue posible preparar la operación.");
    return data;
  }

  async function postJSON(url, payload) {
    const response = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok || data.ok === false) throw new Error(data.error || "No fue posible validar la operación.");
    return data;
  }

  async function registerPasskey() {
    if (!window.PublicKeyCredential) throw new Error("Este navegador no tiene passkeys disponibles.");
    const options = prepareCreationOptions(await getJSON("/maestro/passkey/register/options"));
    const credential = await navigator.credentials.create({ publicKey: options });
    await postJSON("/maestro/passkey/register/verify", credentialToJSON(credential));
    return "Touch ID / passkey quedó registrado para este Centro Maestro.";
  }

  async function loginPasskey() {
    if (!window.PublicKeyCredential) throw new Error("Este navegador no tiene passkeys disponibles.");
    const options = prepareRequestOptions(await getJSON("/maestro/passkey/auth/options"));
    const credential = await navigator.credentials.get({ publicKey: options });
    const result = await postJSON("/maestro/passkey/auth/verify", credentialToJSON(credential));
    window.location.href = result.redirect || "/maestro";
  }

  function bindPasskeyButton(selector, action) {
    const button = document.querySelector(selector);
    const status = document.querySelector("[data-passkey-status]");
    if (!button) return;
    button.addEventListener("click", async () => {
      button.disabled = true;
      if (status) status.textContent = "Esperando confirmación biométrica...";
      try {
        const message = await action();
        if (status) status.textContent = message || "Operación completada.";
      } catch (error) {
        if (status) status.textContent = error.message;
      } finally {
        button.disabled = false;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    bindPasskeyButton("[data-passkey-login]", loginPasskey);
    bindPasskeyButton("[data-passkey-register]", registerPasskey);
  });
}());
