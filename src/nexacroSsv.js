// Nexacro 14 SSV uses RS between records, US between fields, ETX for null.
const RS = "\x1e", US = "\x1f";
const safeId = (id) => /^[A-Za-z_][A-Za-z0-9_]*$/.test(id);
export function parseSsv(text) {
  const lines = text.replace(/^\uFEFF/, "").split(RS);
  if (lines.shift()?.toLowerCase() !== "ssv:utf-8") throw new Error("Expected Nexacro SSV response.");
  const parameters = Object.create(null), datasets = Object.create(null);
  let dataset;
  for (const line of lines) {
    if (!line) continue;
    if (line.startsWith("Dataset:")) {
      const id = line.slice(8);
      if (!safeId(id) || datasets[id]) throw new Error("Invalid SSV dataset identifier.");
      dataset = datasets[id] = { columns: [], rows: [] };
    } else if (line.startsWith("_RowType_")) {
      if (!dataset || dataset.columns.length) throw new Error("Invalid SSV schema.");
      dataset.columns = line.split(US).slice(1).map(c => c.split(":")[0]);
      if (dataset.columns.some(c => !safeId(c)) || new Set(dataset.columns).size !== dataset.columns.length) throw new Error("Invalid SSV columns.");
    } else if (dataset) {
      const [type, ...values] = line.split(US);
      if (!["N", "I", "U"].includes(type) || values.length !== dataset.columns.length) throw new Error("Unexpected SSV row shape.");
      dataset.rows.push(Object.fromEntries(dataset.columns.map((col, i) => [col, values[i] === "\x03" ? null : values[i]])));
    } else {
      for (const p of line.split(US)) {
        const eq = p.indexOf("=");
        if (eq < 0) throw new Error("Invalid SSV parameter.");
        const id = p.slice(0, eq).split(":")[0];
        if (!safeId(id)) throw new Error("Invalid SSV parameter identifier.");
        parameters[id] = p.slice(eq + 1);
      }
    }
  }
  return { parameters, datasets };
}

export function encodeSsv(parameters = {}, datasets = {}) {
  const atom = v => {
    if (v === null || v === undefined) return "\x03";
    const s = String(v);
    if (/[\x03\x1e\x1f]/.test(s)) throw new Error("SSV value contains reserved characters.");
    return s;
  };
  const id = v => { if (!safeId(v)) throw new Error("Invalid SSV identifier."); return v; };
  const lines = ["SSV:utf-8"];
  for (const [k, v] of Object.entries(parameters)) lines.push(`${id(k)}=${atom(v)}`);
  for (const [name, rows] of Object.entries(datasets)) {
    if (!rows.length) throw new Error("Input dataset needs a row.");
    const columns = Object.keys(rows[0]);
    lines.push(`Dataset:${id(name)}`, ["_RowType_", ...columns.map(c => `${id(c)}:STRING(256)`)].join(US));
    for (const row of rows) lines.push(["N", ...columns.map(c => atom(row[c]))].join(US));
  }
  return lines.join(RS) + RS;
}

export async function transaction(http, path, parameters = {}, datasets = {}) {
  const response = await http.request(`https://ef.hira.or.kr/efweb${path}`, {
    method: "POST", body: encodeSsv(parameters, datasets),
    headers: { "Content-Type": "text/plain; charset=UTF-8", Origin: "https://ef.hira.or.kr" },
    referer: "https://ef.hira.or.kr/efweb/index.do?sso=ok",
  });
  const parsed = parseSsv(response.text);
  // The live HIRA success response omits ErrorCode; Nexacro defaults it to zero.
  // Callers must additionally require their expected dataset/schema.
  if (Object.hasOwn(parsed.parameters, "ErrorCode") && parsed.parameters.ErrorCode !== "0") {
    throw new Error("Nexacro transaction reported an error.");
  }
  return parsed;
}
