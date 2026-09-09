// A private stdin pipe is the ownership lease; no persistent daemon/PID adoption.
if (process.stdin.isTTY) {
  console.error("Launch from the menu bar app, not an interactive terminal.");
  process.exit(1);
}
process.stdin.resume();
process.stdin.on("end", () => process.exit(0));
process.stdin.on("error", () => process.exit(1));
const { httpsServer, ssoServer } = await import("../src/server.js");
function status() {
  if (httpsServer.listening && ssoServer.listening) console.log("HIRA_APP_HEALTHY");
}
httpsServer.on("listening", status);
ssoServer.on("listening", status);
status();
setInterval(status, 1000);
