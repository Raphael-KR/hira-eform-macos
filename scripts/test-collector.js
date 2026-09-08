import test from "node:test";
import assert from "node:assert/strict";
import { parseSsv, encodeSsv, transaction } from "../src/nexacroSsv.js";
import { checkedUrl } from "../src/hiraHttp.js";
import { completionTarget, returnForm } from "../src/cliLogin.js";
import { dateRange, collectChuna, RESULT_COLUMNS } from "../src/collectChuna.js";

test("SSV round trip preserves Unicode, leading zeroes and null", () => {
  const row = { name: "\ud64d\uae38\ub3d9", code: "0012", empty: "", absent: null, text: "line\nsecond=a" };
  const result = parseSsv(encodeSsv({ APP_YN: "Y" }, { dsCond: [row] }));
  assert.equal(result.parameters.APP_YN, "Y");
  assert.deepEqual(result.datasets.dsCond.rows, [row]);
});
test("SSV rejects HTML, truncated rows and reserved characters", () => {
  assert.throws(() => parseSsv("<html>login</html>"));
  assert.throws(() => parseSsv("SSV:utf-8\x1eDataset:ds\x1e_RowType_\x1fid:STRING(1)\x1eN\x1e"));
  assert.throws(() => encodeSsv({}, { ds: [{ id: "bad\x1evalue" }] }));
});
test("transaction rejects errors but accepts HIRA's omitted success code", async () => {
  const fake = text => ({ request: async () => ({ text }) });
  await assert.rejects(transaction(fake(encodeSsv({ ErrorCode: "-1" })), "/isLogin.do"));
  assert.ok((await transaction(fake(encodeSsv({}, { ds: [{ id: "1" }] })), "/isLogin.do")).datasets.ds);
});
test("dates are strict and inclusive", () => {
  assert.equal(dateRange("2026-06-01", "2026-09-08").start, "20260601");
  for (const args of [["2026-02-30", "2026-09-08"], ["2026-09-09", "2026-09-08"], ["20260601", "2026-09-08"]]) assert.throws(() => dateRange(...args));
});
test("authentication rejects unrelated destinations without executing scripts", () => {
  for (const url of ["http://ef.hira.or.kr", "https://ef.hira.or.kr.evil.test", "https://secret@ef.hira.or.kr"]) assert.throws(() => checkedUrl(url));
  const base = "https://ef.hira.or.kr/efweb/ksign/login_post_proc.jsp";
  assert.equal(completionTarget('<script>document.location.href="/efweb/pkiLogin.ndo";</script>', base), "https://ef.hira.or.kr/efweb/pkiLogin.ndo");
  assert.throws(() => completionTarget('<script>document.location.href="https://example.org";</script>', base));
  assert.throws(() => completionTarget('<script>document.location.href=getSecret();</script>', base));
  assert.throws(() => returnForm('<form name="pmisso" method="post" action="/delete"><input name="pmi-sso-return" value="synthetic"></form>', base));
  const form = returnForm('<form name="pmisso" method="post" action="/efweb/pkiLogin.ndo"><input name="pmi-sso-return" value="synthetic&amp;value"></form>', base);
  assert.equal(form.fields["pmi-sso-return"], "synthetic&value");
});

const columns = [...RESULT_COLUMNS, "totCnt", "ykiho", "sno", "patHpin"];
function makeRows(count) {
  return Array.from({ length: count }, (_, i) => ({ ...Object.fromEntries(columns.map(c => [c, ""])),
    rn: String(i + 1), totCnt: String(count), ykiho: "00000000", sno: String(i),
    patHpin: "synthetic-internal-id", patNm: "synthetic", diagYr: "2026", diagDd: "20260601",
  }));
}
const args = { http: {}, ykiho: "00000000", from: "2026-06-01", to: "2026-09-08" };
function fakeQuery(rows, mutate = () => {}) {
  return async (_, path, params, { dsCond: [cond] }) => {
    assert.equal(path, "/ie/ier/selectChnaSmitInqL.do");
    assert.equal(cond.diagDdStd, "20260601"); assert.equal(cond.diagDdEnd, "20260908");
    assert.equal(cond.smitDtStd, ""); assert.equal(cond.insupTpCd, "");
    const batch = rows.slice((Number(cond.pageNum) - 1) * 20, Number(cond.pageNum) * 20).map(r => ({ ...r }));
    mutate(batch, cond);
    return { datasets: { dsList: { columns, rows: batch } } };
  };
}
test("collects all pages and omits internal patient/provider identifiers", async () => {
  const result = await collectChuna({ ...args, runTransaction: fakeQuery(makeRows(43)) });
  assert.equal(result.total, 43); assert.deepEqual(result.pages.map(p => p.count), [20, 20, 3]);
  assert.equal(result.rows.length, 43);
  assert.ok(!Object.hasOwn(result.rows[0], "patHpin")); assert.ok(!Object.hasOwn(result.rows[0], "ykiho"));
});
test("explicit empty dsList is zero; missing dataset is not", async () => {
  const result = await collectChuna({ ...args, runTransaction: fakeQuery([]) });
  assert.equal(result.total, 0);
  await assert.rejects(collectChuna({ ...args, runTransaction: async () => ({ datasets: {} }) }));
});
test("rejects count drift, out-of-range dates, mixed accounts and repeated rows", async () => {
  for (const mutate of [
    batch => { batch[0].totCnt = "44"; },
    batch => { batch[0].diagDd = "20260531"; },
    batch => { batch[0].ykiho = "11111111"; },
    batch => { batch[1].sno = batch[0].sno; },
    batch => { batch[0].rn = "99"; },
    batch => { batch.pop(); },
  ]) await assert.rejects(collectChuna({ ...args, runTransaction: fakeQuery(makeRows(43), mutate) }));
});
