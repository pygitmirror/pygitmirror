// The two forms which describe the source and the destination.

import { el } from "./dom.js";

const LABELS = { gitea: "Gitea or Forgejo", gitlab: "GitLab", plain: "Any git server" };
const URL_HINTS = {
  gitea: "http://localhost:3000",
  gitlab: "https://gitlab.com",
  plain: "https://git.example.com",
};

function field(label, input) {
  return el("label", {}, label, input);
}

// Fill a fieldset with the fields of a host, and return a function which
// reads them.
export function buildHost(fieldset, providers) {
  const role = fieldset.dataset.role;
  const provider = el("select", { name: `${role}-provider` });
  for (const item of providers) {
    provider.append(el("option", { value: item.name, text: LABELS[item.name] || item.name }));
  }
  const url = el("input", { type: "url", autocomplete: "off", spellcheck: "false" });
  // "new-password" keeps a password manager from offering to fill or save it.
  const token = el("input", { type: "password", autocomplete: "new-password" });
  const gitUrl = el("input", {
    type: "text",
    autocomplete: "off",
    spellcheck: "false",
    placeholder: "the same address",
  });
  const tokenField = field("Access token", token);
  const urlField = field("Address", url);
  const note = el("p", { class: "hint" });

  function update() {
    const chosen = providers.find((item) => item.name === provider.value);
    url.placeholder = URL_HINTS[provider.value] || "";
    urlField.firstChild.textContent = chosen.default_url ? "Address, if it is your own server" : "Address";
    tokenField.firstChild.textContent = chosen.has_api ? "Access token" : "Access token, if it needs one";
    note.textContent = chosen.has_api
      ? "Repositories are created when they are missing."
      : "Reached through git only: repositories cannot be listed or created, " +
        "so the destination repository must exist. Its address is this address, " +
        "the owner and the name.";
  }
  provider.addEventListener("change", update);

  fieldset.append(
    el("div", { class: "fields two" }, field("Kind of server", provider), urlField),
    el("div", { class: "fields two" }, tokenField, field("Address for git, if it differs", gitUrl)),
    note,
  );
  update();

  return () => ({
    provider: provider.value,
    url: url.value.trim(),
    token: token.value,
    git_url: gitUrl.value.trim(),
  });
}
