import { test } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import net from "node:net";
import { setTimeout as delay } from "node:timers/promises";
import forge from "node-forge";

test("menu host readiness, stop, restart, conflict and missing TLS", { timeout: 20000 }, async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "hira-app-test-"));
  const children = [];
  const blocker = net.createServer();
  try {
    const keys = forge.pki.rsa.generateKeyPair(2048);
    const cert = forge.pki.createCertificate();
    cert.publicKey = keys.publicKey;
    cert.serialNumber = "01";
    cert.validity.notBefore = new Date();
    cert.validity.notAfter = new Date(Date.now() + 86400000);
    cert.setSubject([{ name: "commonName", value: "test-only" }]);
    cert.setIssuer(cert.subject.attributes);
    cert.sign(keys.privateKey, forge.md.sha256.create());
    fs.writeFileSync(path.join(dir, "server.key"), forge.pki.privateKeyToPem(keys.privateKey), { mode: 0o600 });
    fs.writeFileSync(path.join(dir, "server.crt"), forge.pki.certificateToPem(cert));
    function launch(extra = {}) {
      const child = spawn(process.execPath, ["scripts/menubar-agent.js"], {
        env: { PATH: process.env.PATH, HOME: dir, HIRA_TLS_DIR: dir, HIRA_PKI_PORT: "0", HIRA_SSO_PORT: "0", ...extra },
        stdio: ["pipe", "pipe", "pipe"],
      });
      const entry = { child, text: "", exited: false };
      entry.exit = new Promise(resolve => child.once("exit", code => { entry.exited = true; resolve(code); }));
      child.stdout.on("data", data => { entry.text += data; });
      child.stderr.resume();
      children.push(entry);
      return entry;
    }
    async function ready(entry) {
      for (let i = 0; i < 100; i++) {
        if (entry.text.includes("HIRA_APP_HEALTHY")) return;
        assert.equal(entry.exited, false, "host exited before readiness");
        await delay(30);
      }
      assert.fail("readiness timed out");
    }
    for (let i = 0; i < 2; i++) {
      const entry = launch();
      await ready(entry);
      assert.match(entry.text, /listening on wss:/);
      assert.match(entry.text, /listening on https:/);
      entry.child.stdin.end();
      assert.equal(await entry.exit, 0, "stdin EOF must stop owned server");
    }
    await new Promise(resolve => blocker.listen(0, "127.0.0.1", resolve));
    const conflict = launch({ HIRA_PKI_PORT: String(blocker.address().port) });
    assert.notEqual(await conflict.exit, 0);
    assert.equal(blocker.listening, true, "existing listener must remain untouched");
    assert.equal(conflict.text.includes("HIRA_APP_HEALTHY"), false);
    const missing = launch({ HIRA_TLS_DIR: path.join(dir, "missing") });
    assert.notEqual(await missing.exit, 0);
  } finally {
    for (const entry of children) {
      if (!entry.exited) { entry.child.kill(); await entry.exit; }
    }
    if (blocker.listening) await new Promise(resolve => blocker.close(resolve));
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
