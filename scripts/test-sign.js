// Verify signing locally without printing the replayable CMS or certificate DN.
import forge from "node-forge";
import { signDn } from "../src/signer.js";
import fs from "node:fs";
import { certDerToCertObj } from "../src/certInfo.js";
import { findSignCertPairs } from "../src/npkiLocator.js";
import { readCertificatePassword } from "../src/keychain.js";

if (process.argv.length !== 2) {
  console.error("No arguments accepted. Configure macOS Keychain first.");
  process.exit(1);
}
try {
  const pairs = findSignCertPairs();
  if (pairs.length !== 1) throw new Error("Select one certificate.");
  const { subjectDN: dn } = certDerToCertObj(fs.readFileSync(pairs[0].certPath, "binary"), 0);
  const inputB64 = forge.util.encode64(forge.util.encodeUtf8(dn));
  const cms = await signDn({ dn, inputB64, password: readCertificatePassword() });
  forge.asn1.fromDer(forge.util.decode64(cms));
  console.log("Local CMS generation succeeded. No CMS, identity or password printed; no network request made.");
} catch {
  console.error("Local signing failed; check certificate selection and Keychain access.");
  process.exitCode = 1;
}
