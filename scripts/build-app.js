import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

if (process.platform !== "darwin") throw new Error("Build requires macOS and Xcode Command Line Tools");
const root = fileURLToPath(new URL("../", import.meta.url));
const { version } = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
if (!/^\d+\.\d+\.\d+$/.test(version)) throw new Error("App version must be major.minor.patch");
const dist = path.join(root, "dist");
fs.mkdirSync(dist, { recursive: true });
// Each build gets its own directory; an existing installed/running app is untouched.
const build = fs.mkdtempSync(path.join(dist, "build-"));
const app = path.join(build, "HIRA e-Form.app");
const contents = path.join(app, "Contents");
fs.mkdirSync(path.join(contents, "MacOS"), { recursive: true });
fs.mkdirSync(path.join(contents, "Resources"));
const iconset = path.join(build, "AppIcon.iconset");
fs.mkdirSync(iconset);
for (const size of [16, 32, 128, 256, 512]) {
  for (const scale of [1, 2]) {
    const pixels = String(size * scale);
    const name = `icon_${size}x${size}${scale === 2 ? "@2x" : ""}.png`;
    execFileSync("sips", ["-z", pixels, pixels, path.join(root, "macos/assets/AppIcon.png"),
      "--out", path.join(iconset, name)], { stdio: "pipe" });
  }
}
execFileSync("iconutil", ["-c", "icns", iconset, "-o", path.join(contents, "Resources/AppIcon.icns")]);
const arch = process.arch === "arm64" ? "arm64" : "x86_64";
execFileSync("xcrun", ["swiftc", "-parse-as-library", "-swift-version", "5", "-O", "-target", `${arch}-apple-macosx12.0`,
  "-module-cache-path", path.join(dist, "module-cache"), path.join(root, "macos/main.swift"),
  "-o", path.join(contents, "MacOS/HiraEForm")], { stdio: "inherit" });
fs.writeFileSync(path.join(contents, "Info.plist"), `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>HiraEForm</string>
<key>CFBundleIdentifier</key><string>kr.raphael.hira-eform-macos</string>
<key>CFBundleName</key><string>HIRA e-Form</string>
<key>CFBundleIconFile</key><string>AppIcon</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>${version}</string>
<key>CFBundleVersion</key><string>${version}</string>
<key>LSMinimumSystemVersion</key><string>12.0</string>
<key>LSUIElement</key><true/>
<key>NSHighResolutionCapable</key><true/>
</dict></plist>
`);
fs.writeFileSync(path.join(contents, "Resources/Runtime.json"), JSON.stringify({
  projectDirectory: root, nodeExecutable: fs.realpathSync(process.execPath),
}, null, 2));
execFileSync("codesign", ["--force", "--sign", "-", app], { stdio: "inherit" });
execFileSync("codesign", ["--verify", "--strict", app], { stdio: "inherit" });
console.log(`Built (not launched): ${app}`);
