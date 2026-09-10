(function () {
  var key = "quantus_cookie_consent_v1";
  var banner;

  function save(value) {
    try {
      localStorage.setItem(key, JSON.stringify({
        value: value,
        savedAt: new Date().toISOString()
      }));
    } catch (err) {
      document.cookie = key + "=" + encodeURIComponent(value) + "; path=/; max-age=31536000; SameSite=Lax";
    }
    window.quantusCookieConsent = value;
    if (banner) banner.hidden = true;
  }

  function read() {
    try {
      var raw = localStorage.getItem(key);
      if (!raw) return null;
      return JSON.parse(raw).value || null;
    } catch (err) {
      return document.cookie.indexOf(key + "=") >= 0 ? "technical_only" : null;
    }
  }

  function boot() {
    banner = document.getElementById("quantus-cookie-banner");
    if (!banner) return;
    var existing = read();
    if (existing) {
      window.quantusCookieConsent = existing;
      return;
    }
    banner.hidden = false;
    banner.addEventListener("click", function (event) {
      var action = event.target && event.target.getAttribute("data-cookie-action");
      if (action === "accept") save("analytics_allowed");
      if (action === "reject") save("technical_only");
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
