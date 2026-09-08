import fs from "node:fs";
import forge from "node-forge";
import { findSignCertPairs } from "../src/npkiLocator.js";
import { readCertificatePassword } from "../src/keychain.js";
import { loadEncryptedKeyDer, BadPasswordError } from "../src/krPbe.js";

let password;
try {
  const pairs = findSignCertPairs();
  if (pairs.length !== 1) {
    throw new Error("Select exactly one certificate using HIRA_SIGN_CERT and HIRA_SIGN_KEY.");
  }
  password = readCertificatePassword();
  const key = loadEncryptedKeyDer(fs.readFileSync(pairs[0].keyPath, "binary"), password);
  password = undefined;
  const cert = forge.pki.certificateFromAsn1(
    forge.asn1.fromDer(fs.readFileSync(pairs[0].certPath, "binary")),
  );
  if (!key.n.equals(cert.publicKey.n) || !key.e.equals(cert.publicKey.e)) {
    throw new Error("Certificate and private key do not match.");
  }
  console.log("Keychain password: usable; private key: matches certificate. No network request made.");
} catch (error) {
  // No underlying parser errors, paths, key material or captured subprocess output.
  console.error(error instanceof BadPasswordError
    ? "Stored password could not decrypt the private key."
    : "Local credential verification failed; check Keychain access and certificate selection.");
  process.exitCode = 1;
} finally {
  password = undefined;
}
