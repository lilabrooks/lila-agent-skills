/*
 * Compact Theme — Copyright (c) 2026 Lila Brooks
 * SPDX-License-Identifier: BSD-2-Clause
 */

(function () {
  "use strict";

  var root = document.documentElement;
  var storageKey = root.dataset.themeStorageKey || "compact-theme";
  var systemTheme = window.matchMedia("(prefers-color-scheme: light)");

  function readStoredTheme() {
    try {
      var value = window.localStorage.getItem(storageKey);
      return value === "light" || value === "dark" ? value : null;
    } catch (_error) {
      return null;
    }
  }

  function storeTheme(theme) {
    try {
      window.localStorage.setItem(storageKey, theme);
    } catch (_error) {
      // The selected theme still applies for this page view.
    }
  }

  function resolvedTheme() {
    if (root.dataset.theme === "light" || root.dataset.theme === "dark") {
      return root.dataset.theme;
    }
    return systemTheme.matches ? "light" : "dark";
  }

  function updateThemeButtons() {
    var nextTheme = resolvedTheme() === "dark" ? "light" : "dark";
    document.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
      button.hidden = false;
      button.textContent = nextTheme + " mode";
      button.setAttribute("aria-label", "Use " + nextTheme + " mode");
    });
  }

  var declaredTheme = root.dataset.theme;
  if (declaredTheme !== "light" && declaredTheme !== "dark") {
    var storedTheme = readStoredTheme();
    if (storedTheme) root.dataset.theme = storedTheme;
  }

  function bindThemeButtons() {
    document.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
      button.addEventListener("click", function () {
        var nextTheme = resolvedTheme() === "dark" ? "light" : "dark";
        root.dataset.theme = nextTheme;
        storeTheme(nextTheme);
        updateThemeButtons();
        document.dispatchEvent(new CustomEvent("compact-theme-change", { detail: { theme: nextTheme } }));
      });
    });
    updateThemeButtons();
  }

  function languageLabel(code, pre) {
    var language = code.dataset.language || pre.dataset.language || "";
    if (!language) {
      var match = Array.from(code.classList).join(" ").match(/(?:^|\s)language-([\w-]+)/);
      if (match) language = match[1];
    }

    var labels = {
      bash: "Shell",
      sh: "Shell",
      shell: "Shell",
      zsh: "Shell",
      js: "JavaScript",
      javascript: "JavaScript",
      ts: "TypeScript",
      typescript: "TypeScript",
      html: "HTML",
      css: "CSS",
      json: "JSON",
      md: "Markdown",
      markdown: "Markdown",
      py: "Python",
      python: "Python",
      yaml: "YAML",
      yml: "YAML"
    };

    return pre.dataset.codeLabel || code.dataset.codeLabel || labels[language.toLowerCase()] || language || "Code";
  }

  function legacyCopy(text) {
    var field = document.createElement("textarea");
    field.value = text;
    field.setAttribute("readonly", "");
    field.style.position = "fixed";
    field.style.opacity = "0";
    document.body.appendChild(field);
    field.select();
    var copied = document.execCommand("copy");
    field.remove();
    return copied;
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).catch(function () {
        if (!legacyCopy(text)) throw new Error("Copy failed");
      });
    }

    return legacyCopy(text) ? Promise.resolve() : Promise.reject(new Error("Copy failed"));
  }

  function enhanceCodeBlocks() {
    document.querySelectorAll("pre > code").forEach(function (code) {
      var pre = code.parentElement;
      if (pre.hasAttribute("data-no-copy") || code.hasAttribute("data-no-copy")) return;
      if (pre.parentElement && pre.parentElement.classList.contains("compact-code-frame")) return;

      var label = languageLabel(code, pre);
      var frame = document.createElement("div");
      var toolbar = document.createElement("div");
      var language = document.createElement("span");
      var button = document.createElement("button");

      frame.className = "compact-code-frame";
      toolbar.className = "compact-code-toolbar";
      language.className = "compact-code-label";
      language.textContent = label;
      button.className = "compact-copy-button";
      button.type = "button";
      button.textContent = "Copy";
      button.setAttribute("aria-label", "Copy " + label + " code");

      pre.parentNode.insertBefore(frame, pre);
      toolbar.append(language, button);
      frame.append(toolbar, pre);

      button.addEventListener("click", function () {
        var originalLabel = "Copy " + label + " code";
        copyText(code.textContent).then(function () {
          button.textContent = "Copied";
          button.setAttribute("aria-label", label + " code copied");
          window.setTimeout(function () {
            button.textContent = "Copy";
            button.setAttribute("aria-label", originalLabel);
          }, 1800);
        }).catch(function () {
          button.textContent = "Copy failed";
          window.setTimeout(function () {
            button.textContent = "Copy";
          }, 1800);
        });
      });
    });
  }

  function initialize() {
    bindThemeButtons();
    enhanceCodeBlocks();
    root.classList.add("compact-theme-ready");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }

  var handleSystemThemeChange = function () {
    if (!root.dataset.theme) updateThemeButtons();
  };

  if (systemTheme.addEventListener) {
    systemTheme.addEventListener("change", handleSystemThemeChange);
  } else if (systemTheme.addListener) {
    systemTheme.addListener(handleSystemThemeChange);
  }
})();
