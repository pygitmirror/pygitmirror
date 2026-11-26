// The page: wires the forms to the application and shows what it answers.

import { api } from "./api.js";
import { createFlow } from "./backdrop.js";
import { byId, bytes, say } from "./dom.js";
import { buildHost } from "./hosts.js";
import { renderJob } from "./results.js";
import { initTheme } from "./theme.js";

const POLL = 700;
let readSource = () => ({});
let readDestination = () => ({});
let flow = { setRunning() {} };

const operation = () => document.querySelector('input[name="operation"]:checked').value;
const names = () =>
  byId("names")
    .value.split(/[\s,]+/)
    .map((name) => name.trim())
    .filter(Boolean);

function showOptions() {
  for (const option of document.querySelectorAll(".options [data-for]")) {
    option.hidden = option.dataset.for !== operation();
  }
}

function setBusy(busy, name = "idle") {
  for (const id of ["preview", "run", "clear-copies"]) byId(id).disabled = busy;
  flow.setRunning(busy);
  byId("flow-name").textContent = name;
  byId("flow").closest(".panel").classList.toggle("is-running", busy);
}

async function showStorage() {
  try {
    const storage = await api.storage();
    const total = Math.max(1, storage.total);
    byId("storage-path").textContent = storage.path;
    byId("storage-used").style.width = `${Math.min(100, (100 * (total - storage.free)) / total)}%`;
    const low = storage.free < 1024 ** 3;
    byId("storage-meter").classList.toggle("is-low", low);
    byId("storage-text").textContent =
      `${bytes(storage.used)} in ${storage.mirrors} local ${storage.mirrors === 1 ? "copy" : "copies"}, ` +
      `${bytes(storage.free)} free. ` +
      (low ? "Less than 1 GB is free: a large repository will not fit." : "A repository needs as much free space as it is large.");
    byId("storage-text").classList.toggle("is-error", low);
  } catch {
    // The readout is a convenience; the forms work without it.
  }
}

async function listRepositories() {
  const status = byId("list-status");
  say(status, "Listing…");
  try {
    const answer = await api.repositories(readSource(), byId("owner").value.trim());
    byId("names").value = answer.repositories.map((item) => item.name).join("\n");
    const archived = answer.repositories.filter((item) => item.archived).length;
    say(
      status,
      `${answer.repositories.length} repositories` + (archived ? `, ${archived} archived` : "") + ". Remove the ones you do not want.",
      "good",
    );
  } catch (error) {
    say(status, error.message, "error");
  }
}

async function follow(id, dryRun) {
  for (;;) {
    const job = await api.job(id);
    renderJob(job, dryRun);
    if (job.state !== "running") return;
    await new Promise((resolve) => setTimeout(resolve, POLL));
  }
}

async function start(dryRun) {
  const status = byId("run-status");
  const chosen = operation();
  if (!dryRun && chosen === "sync" && !confirm("Sync overwrites the destination. Commits which only the destination has are lost. Continue?")) {
    return;
  }
  say(status, "");
  setBusy(true, dryRun ? `preview of ${chosen}` : chosen);
  try {
    const { id } = await api.start({
      operation: chosen,
      source: readSource(),
      destination: readDestination(),
      owner: byId("owner").value.trim(),
      destination_owner: byId("destination-owner").value.trim(),
      names: names(),
      keep_extra: byId("keep-extra").checked,
      archive_source: byId("archive-source").checked,
      keep_copies: byId("keep-copies").checked,
      dry_run: dryRun,
    });
    byId("results").scrollIntoView({ behavior: "smooth", block: "start" });
    await follow(id, dryRun);
  } catch (error) {
    say(status, error.message, "error");
  } finally {
    setBusy(false);
    showStorage();
  }
}

async function clearCopies() {
  if (!confirm("Delete all local copies? The next sync downloads every repository again.")) return;
  try {
    await api.clearStorage();
  } catch (error) {
    say(byId("run-status"), error.message, "error");
  }
  showStorage();
}

async function init() {
  initTheme();
  flow = createFlow(byId("flow"));
  showOptions();
  for (const input of document.querySelectorAll('input[name="operation"]')) {
    input.addEventListener("change", showOptions);
  }
  byId("list").addEventListener("click", listRepositories);
  byId("preview").addEventListener("click", () => start(true));
  byId("run").addEventListener("click", () => start(false));
  byId("clear-copies").addEventListener("click", clearCopies);
  try {
    const session = await api.session();
    // A version between releases has a suffix which only developers need.
    byId("version").textContent = `v${session.version.split("+")[0]}`;
    readSource = buildHost(document.querySelector('[data-role="source"]'), session.providers);
    readDestination = buildHost(document.querySelector('[data-role="destination"]'), session.providers);
  } catch (error) {
    say(byId("run-status"), error.message, "error");
  }
  showStorage();
}

init();
