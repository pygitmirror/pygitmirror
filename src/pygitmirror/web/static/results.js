// Showing a job: the figures on top and one row per repository.

import { byId, el } from "./dom.js";

function figure(value, caption, mark) {
  return el(
    "li",
    { "data-mark": mark },
    el("span", { class: "num", text: String(value) }),
    el("span", { class: "cap", text: caption }),
  );
}

function tone(result) {
  if (!result) return ["wait", "waiting"];
  if (!result.ok) return ["stop", "failed"];
  const plan = result.plan;
  const changes = plan.create.length + plan.update.length + (result.pruned ? plan.delete.length : 0);
  const any = changes > 0 || result.created || result.archived;
  if (result.dry_run) return any ? ["warn", "would change"] : ["good", "up to date"];
  return any ? ["good", "done"] : ["good", "up to date"];
}

function row(name, result) {
  const [kind, word] = tone(result);
  const title = el("span", { class: "row-name", text: name });
  if (result && result.destination !== result.source) {
    title.append(el("span", { class: "to", text: ` → ${result.destination}` }));
  }
  const item = el(
    "li",
    { class: result && !result.ok ? "is-failed" : "" },
    title,
    el("span", { class: "pill", "data-tone": kind, text: word }),
  );
  if (!result) return item;
  if (result.ok) {
    // The summary starts with the operation and the names, which the row has.
    const text = result.summary.split(": ").slice(1).join(": ");
    // "up to date" is on the pill already.
    if (text !== word) item.append(el("span", { class: "row-text", text }));
  } else if (result.advice) {
    // What to do, with what git or the server said behind a click.
    item.append(
      el("span", { class: "row-text", text: result.advice }),
      el("details", { class: "row-details" }, el("summary", { text: "What the server said" }), el("pre", { text: result.error })),
    );
  } else {
    item.append(el("span", { class: "row-text", text: result.error }));
  }
  return item;
}

export function renderJob(job, dryRun) {
  const results = new Map(job.results.map((result) => [result.source, result]));
  const done = job.results;
  const sum = (pick) => done.reduce((total, result) => total + pick(result), 0);
  const failed = done.filter((result) => !result.ok).length;

  byId("results-title").textContent =
    job.state === "running"
      ? `Working: ${done.length} of ${job.repositories.length}`
      : `${dryRun ? "Preview" : "Finished"}: ${done.length - failed} of ${job.repositories.length} succeeded`;
  byId("results-note").textContent = job.error
    ? job.error
    : dryRun
      ? "This was a preview. Nothing was changed at either server."
      : "Branches and tags, per repository.";

  byId("figures").replaceChildren(
    figure(`${done.length}/${job.repositories.length}`, "repositories processed", "c2"),
    figure(sum((r) => r.plan.create.length), dryRun ? "to create" : "created", "c4"),
    figure(sum((r) => r.plan.update.length), dryRun ? "to update" : "updated", "c1"),
    figure(sum((r) => (r.pruned ? r.plan.delete.length : 0)), dryRun ? "to delete" : "deleted", "c3"),
    figure(failed, "failed", "muted"),
  );
  byId("rows").replaceChildren(...job.repositories.map((name) => row(name, results.get(name))));
}
