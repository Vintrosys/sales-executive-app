"use strict";

(() => {
  const path = window.location.pathname.replace(/\/+$/, "") || "/";
  if (path !== "/desk/sales-executive-app") return;

  if (!document.querySelector('link[rel="manifest"]')) {
    const manifest = document.createElement("link");
    manifest.rel = "manifest";
    manifest.href = "/assets/sales_executive_app/manifest.webmanifest";
    document.head.appendChild(manifest);
  }

  if (!document.querySelector('meta[name="theme-color"]')) {
    const themeColor = document.createElement("meta");
    themeColor.name = "theme-color";
    themeColor.content = "#3346D3";
    document.head.appendChild(themeColor);
  }

  if (!document.querySelector('meta[name="apple-mobile-web-app-capable"]')) {
    const capable = document.createElement("meta");
    capable.name = "apple-mobile-web-app-capable";
    capable.content = "yes";
    document.head.appendChild(capable);
  }

  if (!document.querySelector('link[rel="apple-touch-icon"]')) {
    const appleIcon = document.createElement("link");
    appleIcon.rel = "apple-touch-icon";
    appleIcon.href = "/assets/sales_executive_app/icons/sales-pwa-180.png";
    document.head.appendChild(appleIcon);
  }

  if ("serviceWorker" in navigator && window.isSecureContext) {
    navigator.serviceWorker.register("/sales-worker.js", {scope: "/"})
      .catch(error => console.error("Sales Executive PWA service worker registration failed:", error));
  }
})();
