// The color theme: follow the system, or the choice kept in this browser.

const KEY = "git-mirror-theme";
const root = document.documentElement;

function stored() {
  try {
    return localStorage.getItem(KEY) || "auto";
  } catch {
    return "auto";
  }
}

function apply(mode) {
  if (mode === "light" || mode === "dark") root.dataset.scheme = mode;
  else delete root.dataset.scheme;
  for (const button of document.querySelectorAll(".theme-switch button")) {
    button.setAttribute("aria-pressed", String(button.dataset.mode === mode));
  }
  // Canvases read their colors from the style sheet and must redraw.
  window.dispatchEvent(new Event("themechange"));
}

export function initTheme() {
  apply(stored());
  for (const button of document.querySelectorAll(".theme-switch button")) {
    button.addEventListener("click", () => {
      try {
        localStorage.setItem(KEY, button.dataset.mode);
      } catch {
        // Without storage the choice lasts until the page is closed.
      }
      apply(button.dataset.mode);
    });
  }
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => apply(stored()));
}
