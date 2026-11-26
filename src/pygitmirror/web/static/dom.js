// Building elements. Text from a server, such as a repository name or an
// error, is only ever set as text, never parsed as HTML.

export function el(tag, attributes = {}, ...children) {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) {
    if (value === false || value === null || value === undefined) continue;
    if (name === "class") node.className = value;
    else if (name === "text") node.textContent = value;
    else node.setAttribute(name, value === true ? "" : value);
  }
  for (const child of children) {
    node.append(child);
  }
  return node;
}

export const byId = (id) => document.getElementById(id);

// Show a message below a form, as an error, a success or a plain note.
export function say(node, message, kind = "") {
  node.textContent = message;
  node.classList.toggle("is-error", kind === "error");
  node.classList.toggle("is-good", kind === "good");
}

export function bytes(count) {
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = count;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value >= 100 || unit === 0 ? Math.round(value) : value.toFixed(1)} ${units[unit]}`;
}
