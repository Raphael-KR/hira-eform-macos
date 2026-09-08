import fs from "node:fs";
import forge from "node-forge";
import * as cheerio from "cheerio";
import { parse } from "acorn";
import { checkedUrl, HiraHttp } from "./hiraHttp.js";
import { findSignCertPairs } from "./npkiLocator.js";
import { certDerToCertObj } from "./certInfo.js";
import { signDn } from "./signer.js";
import { loadEncryptedKeyDer } from "./krPbe.js";
import { readCertificatePassword } from "./keychain.js";
import { transaction } from "./nexacroSsv.js";

export function completionTarget(html, base) {
  const $ = cheerio.load(html), targets = new Set();
  const walk = node => {
    if (!node || typeof node !== "object") return;
    const left = node.left;
    if (node.type === "AssignmentExpression" && node.operator === "=" &&
        left?.type === "MemberExpression" && !left.computed && left.property.name === "href" &&
        left.object?.type === "MemberExpression" && !left.object.computed &&
        left.object.object?.name === "document" && left.object.property?.name === "location" &&
        node.right.type === "Literal" && typeof node.right.value === "string") {
      targets.add(checkedUrl(node.right.value, base).href);
    }
    for (const child of Object.values(node)) {
      if (Array.isArray(child)) child.forEach(walk);
      else if (child && typeof child === "object") walk(child);
    }
  };
  // Parse syntax only: never execute server-provided JavaScript.
  $("script:not([src])").each((_, script) => walk(parse($(script).html() || "", { ecmaVersion: "latest" })));
  if (targets.size !== 1) throw new Error("Unrecognized login completion page.");
  const target = checkedUrl([...targets][0]);
  if (target.origin !== "https://ef.hira.or.kr" || target.pathname !== "/efweb/pkiLogin.ndo") {
    throw new Error("Unexpected login completion destination.");
  }
  return target.href;
}

export function returnForm(html, base) {
  const $ = cheerio.load(html), form = $('form[name="pmisso"]');
  if (!form.length) return null;
  if (form.length !== 1 || form.attr("method")?.toLowerCase() !== "post") throw new Error("Unexpected SSO form.");
  const url = checkedUrl(form.attr("action"), base);
  if (url.origin !== "https://ef.hira.or.kr" || url.pathname !== "/efweb/pkiLogin.ndo") throw new Error("Unexpected SSO return destination.");
  const fields = Object.fromEntries(form.find("input[name]").toArray().map(input => [$(input).attr("name"), $(input).attr("value") || ""]));
  const keys = Object.keys(fields);
  if (keys.length !== 1 || !["pmi-sso-return", "pmi-sso-return2"].includes(keys[0]) || !fields[keys[0]]) throw new Error("Unexpected SSO return fields.");
  return { url: url.href, fields };
}

export async function loginFromKeychain() {
  // Do not silently sign with another cert when an explicit path is misspelled.
  for (const name of ["HIRA_SIGN_CERT", "HIRA_SIGN_KEY"]) {
    if (process.env[name] && !fs.existsSync(process.env[name])) throw new Error("Invalid explicit certificate path.");
  }
  const pairs = findSignCertPairs();
  if (pairs.length !== 1) throw new Error("Select exactly one certificate with HIRA_SIGN_CERT and HIRA_SIGN_KEY.");
  const certBytes = fs.readFileSync(pairs[0].certPath, "binary");
  const cert = forge.pki.certificateFromAsn1(forge.asn1.fromDer(certBytes));
  const now = new Date();
  if (now < cert.validity.notBefore || now > cert.validity.notAfter) throw new Error("Certificate is outside its validity period.");
  let password = readCertificatePassword(), cms;
  try {
    const key = loadEncryptedKeyDer(fs.readFileSync(pairs[0].keyPath, "binary"), password);
    if (!key.n.equals(cert.publicKey.n) || !key.e.equals(cert.publicKey.e)) throw new Error("Certificate/key mismatch.");
    const { subjectDN } = certDerToCertObj(certBytes, 0);
    cms = await signDn({ dn: subjectDN, inputB64: forge.util.encode64(forge.util.encodeUtf8(subjectDN)), password });
  } finally {
    password = undefined;
  }
  const http = new HiraHttp();
  const loginPage = "https://ef.hira.or.kr/efweb/kcase/pkiLogin.jsp";
  await http.request(loginPage);
  let page = await http.postForm("https://extsso.hira.or.kr/sso/pmi-sso-login-certificate.jsp", {
    gid: "hira_efinter1", signeddata: cms,
    returl: "https://ef.hira.or.kr/efweb/pkiLogin.ndo?signeddata=" + cms,
  }, loginPage);
  cms = undefined;
  let forms = 0;
  for (; forms < 4; forms++) {
    const form = returnForm(page.text, page.url);
    if (!form) break;
    page = await http.postForm(form.url, form.fields, page.url);
  }
  if (forms === 4 || new URL(page.url).pathname !== "/efweb/ksign/login_post_proc.jsp") throw new Error("SSO login did not reach its completion page.");
  // Local KAccess token storage is not needed by this process-local cookie session.
  // The site's success and failure branches both navigate to this same target.
  await http.request(completionTarget(page.text, page.url));
  const session = await transaction(http, "/isLogin.do", { APP_YN: "Y" });
  const users = session.datasets.gdsUserInfo?.rows;
  const menu = session.datasets.gdsMenu?.rows;
  if (users?.length !== 1 || !/^\d{8}$/.test(users[0].ykiho || "") || !menu?.some(row => row.menuId === "EF05010002")) {
    throw new Error("Authenticated institution or Chuna menu could not be verified.");
  }
  return { http, ykiho: users[0].ykiho };
}
