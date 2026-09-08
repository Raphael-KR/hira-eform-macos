import { transaction } from "./nexacroSsv.js";

export const RESULT_COLUMNS = ["rn", "diagYr", "diagDd", "smitDt", "patNm", "patBth",
  "insupTpCd", "insupTpCdNm", "acdtRcvNo", "maidclCd", "maidclCdNm", "oinjTpCd",
  "oinjTpCdNm", "payYn", "delYn", "delDataTpCdNm"];

export function dateRange(from, to) {
  for (const value of [from, to]) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value || "")) throw new Error("Dates must use YYYY-MM-DD.");
    const date = new Date(value + "T00:00:00Z");
    if (Number.isNaN(date.valueOf()) || date.toISOString().slice(0, 10) !== value) throw new Error("Invalid calendar date.");
  }
  if (from > to) throw new Error("Start date must not follow end date.");
  return { from, to, start: from.replaceAll("-", ""), end: to.replaceAll("-", "") };
}

export async function collectChuna({ http, ykiho, from, to, onPage = () => {}, runTransaction = transaction }) {
  const range = dateRange(from, to);
  const pageSize = 20, rows = [], seen = new Set(), pages = [];
  let total;
  for (let pageNum = 1; pageNum <= 10000; pageNum++) {
    const result = await runTransaction(http, "/ie/ier/selectChnaSmitInqL.do", {}, { dsCond: [{
      ykiho, patNm: "", patBth: "", diagDdStd: range.start, diagDdEnd: range.end,
      smitDtStd: "", smitDtEnd: "", fetchRow: String(pageSize), pageNum: String(pageNum),
      insupTpCd: "", payYn: "", acdtRcvNo: "",
    }] });
    const list = result.datasets.dsList;
    if (!list || (list.rows.length && RESULT_COLUMNS.concat("totCnt", "ykiho", "sno", "patHpin").some(c => !list.columns.includes(c)))) {
      throw new Error("Missing or changed Chuna result schema.");
    }
    const batch = list.rows;
    if (total === undefined) {
      if (batch.length && !/^\d+$/.test(batch[0].totCnt || "")) throw new Error("Invalid total count.");
      total = batch.length ? Number(batch[0].totCnt) : 0;
      if (!Number.isSafeInteger(total) || total > pageSize * 10000) throw new Error("Result count exceeds collection limit.");
    }
    if (batch.length !== Math.min(pageSize, total - rows.length)) throw new Error("Page size does not match server total.");
    for (const row of batch) {
      if (Number(row.totCnt) !== total || row.ykiho !== ykiho) throw new Error("Result total or account changed during collection.");
      if (!/^\d{8}$/.test(row.diagDd || "") || row.diagDd < range.start || row.diagDd > range.end) throw new Error("Result is outside requested treatment dates.");
      if (Number(row.rn) !== rows.length + 1) throw new Error("Result row sequence is discontinuous.");
      const key = JSON.stringify([row.ykiho, row.diagYr, row.diagDd, row.patHpin, row.sno]);
      if (seen.has(key)) throw new Error("Duplicate record across result pages.");
      seen.add(key);
      // Keep visible query fields, not internal patient IDs, provider IDs or tokens.
      rows.push(Object.fromEntries(RESULT_COLUMNS.map(c => [c, row[c]])));
    }
    pages.push({ page: pageNum, count: batch.length, serverTotal: total });
    onPage(pages.at(-1));
    if (rows.length === total) return { range: { from, to, inclusive: true, field: "diagDd" }, total, pages, rows };
  }
  throw new Error("Page limit reached before completing collection.");
}
