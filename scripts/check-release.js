// Check tracked AND new publication candidates; ignored local data is never read.
import fs from "node:fs";
import { execFileSync } from "node:child_process";

export function inspectCandidate(name, content = "") {
  const issues = [];
  const allowed = /^(?:\.gitignore|README\.md|package(?:-lock)?\.json|src\/[\w-]+\.js|scripts\/[\w-]+\.(?:js|swift)|docs\/[\w-]+\.(?:md|txt)|\.github\/workflows\/[\w-]+\.ya?ml)$/;
  const ddmdSource = /^ddmd\/(?:README\.md|docs\/[\w-]+\.md|gateway_poc\/(?:README\.md|(?:auto-update|gateway|isolated-ui(?:\/app-launcher)?|live|macos-jvm|scripts|src|update|wine)\/[\w-]+\.(?:java|py|mjs|md|command)))$/;
  if (!allowed.test(name) && !ddmdSource.test(name)) issues.push("file is outside the public source allowlist");
  if (/-----BEGIN (?:[A-Z ]*PRIVATE KEY|CERTIFICATE)-----/.test(content)) issues.push("embedded PEM credential");
  if (/["'][A-Za-z0-9+/]{256,}={0,2}["']/.test(content)) issues.push("large embedded base64 value needs review");
  if (/\/Users\/(?!<|example\b)[A-Za-z0-9_.-]+\//.test(content)) issues.push("owner-specific absolute path");
  if (/\b\d{6}-[1-8]\d{6}\b/.test(content)) issues.push("possible resident registration number");
  return issues;
}

if (process.argv[1] && new URL(import.meta.url).pathname === process.argv[1]) {
  const paths = [...new Set(execFileSync("git", ["ls-files", "--cached", "--others", "--exclude-standard", "-z"], { encoding: "utf8" }).split("\0").filter(Boolean))];
  let checked = 0, failed = 0;
  for (const name of paths) {
    if (!fs.existsSync(name)) continue; // Pending deletion, not a release file.
    const stat = fs.lstatSync(name);
    const issues = stat.isSymbolicLink() || !stat.isFile() ? ["non-regular file"] : inspectCandidate(name);
    // Do not read data/credentials even if someone accidentally stages them.
    if (!issues.length) issues.push(...inspectCandidate(name, fs.readFileSync(name, "utf8")));
    checked++;
    for (const issue of issues) { console.error(`${name}: ${issue}`); failed++; }
  }
  console.log(`Public candidate check: ${checked} files, ${failed} findings. Ignored data was not read.`);
  process.exitCode = failed ? 1 : 0;
}
