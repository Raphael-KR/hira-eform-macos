// Full integration test: server loads a synthetic encrypted key, client performs the
// entire bootstrap + CERT_GENERATE_SIGNDATA, then openssl validates the returned CMS.
import forge from "node-forge";
import "../src/seed.js";
import WebSocket from "ws";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync, spawn } from "node:child_process";

const PW = "testpw1234";
const DN = "C=KR,O=TEST,CN=integration-0000000000000000";

// --- prepare cert + encrypted key ---
const keys = forge.pki.rsa.generateKeyPair(2048);
const cert = forge.pki.createCertificate();
cert.publicKey = keys.publicKey;
cert.serialNumber = "01";
cert.validity.notBefore = new Date();
cert.validity.notAfter = new Date(Date.now() + 365 * 86400_000);
const attrs = DN.split(",").map((p) => {
  const [k, v] = p.split("=");
  return { shortName: k, value: v };
});
cert.setSubject(attrs);
cert.setIssuer(attrs);
cert.sign(keys.privateKey, forge.md.sha256.create());

const pkcs8Bytes = forge.asn1.toDer(
  forge.pki.wrapRsaPrivateKey(forge.pki.privateKeyToAsn1(keys.privateKey)),
).getBytes();

const salt = forge.random.getBytesSync(16);
const iter = 2048;
const iv = forge.random.getBytesSync(16);
const derivedKey = forge.pkcs5.pbkdf2(forge.util.encodeUtf8(PW), salt, iter, 16, forge.md.sha1.create());
const c = forge.cipher.createCipher("SEED-CBC", derivedKey);
c.start({ iv });
c.update(forge.util.createBuffer(pkcs8Bytes));
c.finish();
const ciphertext = c.output.getBytes();

const asn1 = forge.asn1;
const oid = (o) => asn1.create(asn1.Class.UNIVERSAL, asn1.Type.OID, false, asn1.oidToDer(o).getBytes());
const intAsn1 = (n) => {
  let hex = n.toString(16);
  if (hex.length % 2) hex = "0" + hex;
  return asn1.create(asn1.Class.UNIVERSAL, asn1.Type.INTEGER, false, forge.util.hexToBytes(hex));
};
const octet = (b) => asn1.create(asn1.Class.UNIVERSAL, asn1.Type.OCTETSTRING, false, b);

const epki = asn1.create(asn1.Class.UNIVERSAL, asn1.Type.SEQUENCE, true, [
  asn1.create(asn1.Class.UNIVERSAL, asn1.Type.SEQUENCE, true, [
    oid("1.2.840.113549.1.5.13"),
    asn1.create(asn1.Class.UNIVERSAL, asn1.Type.SEQUENCE, true, [
      asn1.create(asn1.Class.UNIVERSAL, asn1.Type.SEQUENCE, true, [
        oid("1.2.840.113549.1.5.12"),
        asn1.create(asn1.Class.UNIVERSAL, asn1.Type.SEQUENCE, true, [octet(salt), intAsn1(iter)]),
      ]),
      asn1.create(asn1.Class.UNIVERSAL, asn1.Type.SEQUENCE, true, [
        oid("1.2.410.200004.1.4"),
        octet(iv),
      ]),
    ]),
  ]),
  octet(ciphertext),
]);

const dir = fs.mkdtempSync(path.join(os.tmpdir(), "hira-full-"));
fs.chmodSync(dir, 0o700);
const certPath = path.join(dir, "signCert.der");
const keyPath = path.join(dir, "signPri.key");
fs.writeFileSync(certPath, Buffer.from(forge.asn1.toDer(forge.pki.certificateToAsn1(cert)).getBytes(), "binary"));
fs.writeFileSync(keyPath, Buffer.from(forge.asn1.toDer(epki).getBytes(), "binary"));

// --- spawn server with env ---
fs.writeFileSync(path.join(dir, "server.key"), forge.pki.privateKeyToPem(keys.privateKey), { mode: 0o600 });
fs.writeFileSync(path.join(dir, "server.crt"), forge.pki.certificateToPem(cert), { mode: 0o600 });
const env = { ...process.env, HIRA_SIGN_CERT: certPath, HIRA_SIGN_KEY: keyPath,
  HIRA_TLS_DIR: dir, HIRA_PKI_PORT: "0", HIRA_SSO_PORT: "0", HIRA_DEBUG: "1" };
const srv = spawn(process.execPath, [path.resolve("src/server.js")], { env, stdio: ["ignore", "pipe", "pipe"] });
const serverExited = new Promise(resolve => srv.once("exit", resolve));
let serverOutput = "";
srv.stdout.on("data", d => { serverOutput += d.toString(); });
srv.stdout.on("data", (d) => process.stdout.write("[srv] " + d));
srv.stderr.on("data", (d) => process.stderr.write("[srv-err] " + d));
let port;
try {
  port = await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("Server startup timed out")), 5000);
    srv.once("error", reject);
    srv.once("exit", () => { clearTimeout(timer); reject(new Error("Server exited before ready")); });
    srv.stdout.on("data", () => {
      const match = serverOutput.match(/listening on wss:\/\/127\.0\.0\.1:(\d+)/);
      if (match) { clearTimeout(timer); resolve(Number(match[1])); }
    });
  });
} catch {
  srv.kill();
  await serverExited;
  fs.rmSync(dir, { recursive: true, force: true });
  throw new Error("Isolated integration server failed to start.");
}

// --- client: run bootstrap, then CERT_GENERATE_SIGNDATA ---
const ws = new WebSocket(`wss://127.0.0.1:${port}/`, { rejectUnauthorized: false });
const sessionKeyId = forge.random.getBytesSync(16);
let rsaPubKey, sessionId, seedKey, seedIv;
let step = "open";

function sendEnv(method, sessId, sendObj, secure = false) {
  const inner = JSON.stringify(sendObj);
  let data;
  if (!secure) {
    data = sendObj.APIName === 0 ? inner : sessionKeyId + inner;
  } else {
    const nonce = forge.util.encode64(forge.random.getBytesSync(8));
    const plain = nonce + forge.util.encode64(inner);
    const cc = forge.cipher.createCipher("SEED-CBC", seedKey);
    cc.start({ iv: seedIv });
    cc.update(forge.util.createBuffer(plain));
    cc.finish();
    data = sessionKeyId + cc.output.getBytes();
  }
  ws.send("1data=" + JSON.stringify({ SessionId: sessId, Data: forge.util.encode64(data), Method: method }));
}

let finished = false;
async function finish(ok) {
  if (finished) return;
  finished = true;
  ws.close();
  srv.kill();
  await serverExited;
  if (serverOutput.includes(PW) || serverOutput.includes("FULL_TEST!") || serverOutput.includes("resp =")) ok = false;
  fs.rmSync(dir, { recursive: true, force: true });
  process.exit(ok ? 0 : 1);
}

ws.on("open", () => {
  ws.send("0open");
  // The real agent does not acknowledge 0open. Start CHECK_INSTALL immediately.
  step = "check";
  sendEnv("install", "kcase", { APIName: 0 });
});

ws.on("message", (buf) => {
  const msg = JSON.parse(buf.toString());
  if (step === "check") {
    step = "init";
    sendEnv("post", forge.util.encode64("FULL_TEST!1!2"), {
      APIName: 1, Version: "1.3.28", Config: '""', ubikeyVer: "x", ubiurl: "", maxpwdcnt: 5,
    });
  } else if (step === "init") {
    rsaPubKey = forge.pki.publicKeyFromAsn1(forge.asn1.fromDer(forge.util.decode64(msg.PubKey)));
    sessionId = msg.SessionId;
    seedKey = forge.random.getBytesSync(16);
    seedIv = forge.random.getBytesSync(16);
    const nonce32 = forge.random.getBytesSync(32);
    const encKey = rsaPubKey.encrypt(seedKey + seedIv + nonce32, "RSAES-PKCS1-V1_5");
    step = "hs";
    sendEnv("post", sessionId, { APIName: 2, EncryptedKey: forge.util.encode64(encKey) });
  } else if (step === "hs") {
    // skip HandshakeMsg verification (the unit test covers it); go straight to sign
    step = "sign";
    const inputB64 = forge.util.encode64(forge.util.encodeUtf8(DN));
    sendEnv("post", sessionId, {
      APIName: 21, Media: "HDD", CertDn: inputB64, CertSn: "1",
      Password: PW, Algorithm: "RSA_PKCS", KeyBit: 2048, Hash: "SHA256",
      Input: inputB64,
    }, true);
  } else if (step === "sign") {
    const d = forge.cipher.createDecipher("SEED-CBC", seedKey);
    d.start({ iv: seedIv });
    d.update(forge.util.createBuffer(forge.util.decode64(msg.Output)));
    d.finish();
    const inner = JSON.parse(d.output.getBytes());
    console.log("[client] sign response Status=", inner.Status, "Output.len=", inner.Output?.length);
    if (inner.Status !== 0) { console.error("sign failed"); finish(false); return; }

    // verify with openssl
    const cmsPath = path.join(dir, "out.cms");
    const contentPath = path.join(dir, "out.content");
    const certPem = path.join(dir, "cert.pem");
    fs.writeFileSync(cmsPath, Buffer.from(forge.util.decode64(inner.Output), "binary"));
    fs.writeFileSync(contentPath, forge.util.encodeUtf8(DN));
    fs.writeFileSync(certPem, forge.pki.certificateToPem(cert));
    try {
      execFileSync("openssl", [
        "cms", "-verify", "-in", cmsPath, "-inform", "der",
        "-certfile", certPem, "-CAfile", certPem,
        "-purpose", "any", "-no_check_time",
      ], { stdio: ["ignore", "pipe", "pipe"] });
      console.log("\n✅ full integration OK — CMS from emulator verifies with openssl");
      finish(true);
    } catch (e) {
      console.error("openssl failed:", e.stderr?.toString() || e.message);
      finish(false);
    }
  }
});

ws.on("error", (e) => { console.error("ws error:", e); finish(false); });
setTimeout(() => { console.error("timeout"); finish(false); }, 15000);
