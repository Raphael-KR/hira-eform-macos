import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import { createHash } from "node:crypto";
import { loginFromKeychain } from "../src/cliLogin.js";
import { collectChuna, dateRange } from "../src/collectChuna.js";

process.umask(0o077);
let phase = "arguments";
try {
  const { values } = parseArgs({ options: { from: { type: "string" }, to: { type: "string" }, help: { type: "boolean" } }, strict: true });
  if (values.help) {
    console.log("Usage: npm run collect:chuna -- --from YYYY-MM-DD --to YYYY-MM-DD\nPassword: macOS Keychain only. Output: private, ignored tmp/ directory.");
  } else {
    dateRange(values.from, values.to);
    phase = "authentication";
    console.log("Authenticating with macOS Keychain (secret values are not logged)...");
    const { http, ykiho } = await loginFromKeychain();
    console.log("Authenticated institution and Chuna query menu verified.");
    phase = "query";
    const result = await collectChuna({ http, ykiho, from: values.from, to: values.to,
      onPage: ({ page, count, serverTotal }) => console.log(`Page ${page}: ${count} rows; server total ${serverTotal}.`),
    });
    phase = "save";
    const root = fileURLToPath(new URL("../tmp/", import.meta.url));
    if (!fs.existsSync(root)) fs.mkdirSync(root, { mode: 0o700 });
    if (!fs.lstatSync(root).isDirectory() || fs.lstatSync(root).isSymbolicLink()) throw new Error("Unsafe output directory.");
    const directory = fs.mkdtempSync(path.join(root, `chuna-${values.from.replaceAll("-", "")}-${values.to.replaceAll("-", "")}-`));
    fs.chmodSync(directory, 0o700);
    const data = JSON.stringify({ source: "https://ef.hira.or.kr/efweb/ie/ier/selectChnaSmitInqL.do",
      menuId: "EF05010002", collectedAt: new Date().toISOString(), ...result }, null, 2) + "\n";
    const output = path.join(directory, "results.json");
    fs.writeFileSync(output, data, { mode: 0o600, flag: "wx" });
    const saved = fs.readFileSync(output);
    const sha256 = createHash("sha256").update(data).digest("hex");
    if (JSON.parse(saved).rows.length !== result.total || createHash("sha256").update(saved).digest("hex") !== sha256) throw new Error("Saved result verification failed.");
    const receipt = { complete: true, treatmentDates: result.range, count: result.total,
      pages: result.pages, validated: ["authenticated-institution", "authorized-menu", "total-count", "row-sequence", "unique-records", "treatment-date-range"],
      sha256, output: "results.json" };
    fs.writeFileSync(path.join(directory, "receipt.json"), JSON.stringify(receipt, null, 2) + "\n", { mode: 0o600, flag: "wx" });
    console.log(`Collection complete: ${result.total} rows, ${values.from} through ${values.to}.`);
    console.log(`Private result: ${output}`);
  }
} catch {
  // Errors from HTTP/crypto libraries may embed tokens, raw bytes or private paths.
  console.error(`Collection failed during ${phase}. No completion is claimed. Check dates, Keychain access, certificate selection and HIRA availability.`);
  process.exitCode = 1;
}
