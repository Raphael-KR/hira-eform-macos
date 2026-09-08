import { CookieJar } from "tough-cookie";

const origins = new Set(["https://ef.hira.or.kr", "https://extsso.hira.or.kr"]);
export function checkedUrl(value, base) {
  const url = new URL(value, base);
  if (!origins.has(url.origin) || url.username || url.password) {
    throw new Error("HTTP destination is outside the authorized HIRA origins.");
  }
  return url;
}

export class HiraHttp {
  jar = new CookieJar();
  async request(value, { method = "GET", body, headers = {}, referer } = {}) {
    let url = checkedUrl(value);
    for (let hop = 0; hop < 12; hop++) {
      const cookie = await this.jar.getCookieString(url.href);
      let response;
      try {
        response = await fetch(url, {
          method, body, redirect: "manual", signal: AbortSignal.timeout(30000),
          headers: { "User-Agent": "Mozilla/5.0", ...headers,
            ...(cookie ? { Cookie: cookie } : {}),
            ...(referer ? { Referer: checkedUrl(referer).href } : {}),
          },
        });
      } catch {
        throw new Error(`HTTPS request failed: ${url.hostname}${url.pathname}`);
      }
      for (const cookieValue of response.headers.getSetCookie()) {
        await this.jar.setCookie(cookieValue, url.href);
      }
      if ([301, 302, 303, 307, 308].includes(response.status)) {
        const location = response.headers.get("location");
        await response.body?.cancel();
        if (!location) throw new Error("Redirect has no destination.");
        url = checkedUrl(location, url);
        if (response.status === 303 || ([301, 302].includes(response.status) && method === "POST")) {
          method = "GET"; body = undefined; headers = {};
        }
        continue;
      }
      if (!response.ok) {
        await response.body?.cancel();
        throw new Error(`HTTP ${response.status}: ${url.pathname}`);
      }
      return { url: url.href, text: await response.text(), type: response.headers.get("content-type") || "" };
    }
    throw new Error("Too many authentication redirects.");
  }
  postForm(url, fields, referer) {
    return this.request(url, { method: "POST", body: new URLSearchParams(fields).toString(),
      headers: { "Content-Type": "application/x-www-form-urlencoded", Origin: new URL(referer).origin }, referer });
  }
}
