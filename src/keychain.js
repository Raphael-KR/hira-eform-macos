import { execFileSync } from "node:child_process";

// Capture into a private pipe, never inherit stdout or put the password in argv.
export function readCertificatePassword() {
  let bytes;
  try {
    bytes = execFileSync("/usr/bin/security", [
      "find-generic-password",
      "-s", "hira-eform-macos.certificate-password",
      "-a", "local-certificate",
      "-w",
    ], { stdio: ["ignore", "pipe", "pipe"], timeout: 30000, maxBuffer: 65536 });
    // security appends one newline; do not trim meaningful password whitespace.
    const end = bytes.at(-1) === 10 ? bytes.length - 1 : bytes.length;
    if (end === 0) throw new Error("empty password");
    return bytes.subarray(0, end).toString("utf8");
  } catch {
    // Child-process errors can contain captured stdout, so never expose the cause.
    throw new Error("Certificate password unavailable from macOS Keychain.");
  } finally {
    bytes?.fill(0);
  }
}
