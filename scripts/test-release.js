import test from "node:test";
import assert from "node:assert/strict";
import { inspectCandidate } from "./check-release.js";

test("publication check rejects data, credentials and unknown paths", () => {
  for (const file of ["tmp/results.json", "results.json", "docs/receipt.json", "signPri.key", ".env", "recon/capture.jsonl", "notes.txt"]) {
    assert.ok(inspectCandidate(file).length);
  }
});
test("publication check allows code but rejects embedded secret-shaped content", () => {
  assert.deepEqual(inspectCandidate("src/example.js", "export const version = 1;"), []);
  assert.ok(inspectCandidate("src/example.js", '"' + "A".repeat(300) + '"').length);
  assert.ok(inspectCandidate("README.md", ["-----BEGIN", "PRIVATE KEY-----"].join(" ")).length);
  assert.ok(inspectCandidate("README.md", ["/Users", "synthetic-owner", "file"].join("/")).length);
});

test("DDMD publication allows first-party sources but excludes runtime and evidence", () => {
  for (const path of ["ddmd/gateway_poc/auto-update/auto_update.py", "ddmd/gateway_poc/isolated-ui/GuiBootstrap.java", "ddmd/docs/ddmd-macos-update-test.md"]) assert.deepEqual(inspectCandidate(path), []);
  for (const path of [".local/ddmd/institution.txt", "ddmd/gateway_poc/evidence/result.json", "ddmd/gateway_poc/private-downloads/notice.zip", "ddmd/gateway_poc/update/prepared.json", "ddmd/gateway_poc/isolated-ui/app-launcher/launcher.m", "ddmd/gateway_poc/lib/vendor.jar"]) assert.ok(inspectCandidate(path).length);
});
