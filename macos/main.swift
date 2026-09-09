import AppKit
import Foundation
import Darwin

struct RuntimeConfig: Codable {
    let projectDirectory: String
    let nodeExecutable: String
}

enum AgentState: String {
    case stopped = "서버 꺼짐"
    case starting = "서버 시작 중"
    case running = "서버 켜짐"
    case stopping = "서버 종료 중"
    case blocked = "다른 프로세스가 포트 사용 중"
    case failed = "서버 오류"
}

// A bind probe checks availability without reading or controlling another server.
func portAvailable(_ port: UInt16) -> Bool {
    let fd = socket(AF_INET, SOCK_STREAM, 0)
    guard fd >= 0 else { return false }
    defer { Darwin.close(fd) }
    var reuse: Int32 = 1
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &reuse, socklen_t(MemoryLayout.size(ofValue: reuse)))
    var address = sockaddr_in()
    address.sin_len = UInt8(MemoryLayout<sockaddr_in>.size)
    address.sin_family = sa_family_t(AF_INET)
    address.sin_port = port.bigEndian
    address.sin_addr.s_addr = inet_addr("127.0.0.1")
    return withUnsafePointer(to: &address) {
        $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
            Darwin.bind(fd, $0, socklen_t(MemoryLayout<sockaddr_in>.size)) == 0
        }
    }
}

@MainActor
final class AgentController {
    private(set) var state: AgentState = .stopped
    private(set) var detail = "PKI 8443 · SSO 39091"
    var changed: (() -> Void)?
    var stopped: (() -> Void)?
    private var child: Process?
    private var input: Pipe?
    private var output: Pipe?
    private var buffer = Data()
    private var lastHealthy = Date.distantPast
    private let config: RuntimeConfig?

    init(config: RuntimeConfig?) { self.config = config }
    var ownsProcess: Bool { child != nil }
    var canStart: Bool { child == nil && state != .blocked }

    private func set(_ value: AgentState, _ message: String? = nil) {
        let nextDetail = message ?? "PKI 8443 · SSO 39091"
        guard state != value || detail != nextDetail else { return }
        state = value
        detail = nextDetail
        changed?()
    }

    func refresh() {
        if let process = child {
            if state == .running && (!process.isRunning || Date().timeIntervalSince(lastHealthy) > 5) {
                set(.failed, "서버 응답 없음 · 중지 후 다시 시작하세요")
            }
        } else if !portAvailable(8443) || !portAvailable(39091) {
            set(.blocked, "기존 터미널 서버를 먼저 종료하세요")
        } else if state == .blocked {
            set(.stopped)
        }
    }

    func start() {
        guard child == nil else { return }
        guard portAvailable(8443), portAvailable(39091) else {
            set(.blocked, "기존 터미널 서버를 먼저 종료하세요")
            return
        }
        guard let config else { set(.failed, "앱 설정 없음 · 앱을 다시 빌드하세요"); return }
        let root = URL(fileURLWithPath: config.projectDirectory)
        let files = ["scripts/menubar-agent.js", "src/server.js", "certs/server.key", "certs/server.crt", "node_modules/ws/package.json"]
        guard FileManager.default.isExecutableFile(atPath: config.nodeExecutable),
              files.allSatisfy({ FileManager.default.fileExists(atPath: root.appendingPathComponent($0).path) }) else {
            set(.failed, "Node·프로젝트·TLS 인증서 설정을 확인하세요")
            return
        }
        let process = Process(), stdin = Pipe(), stdout = Pipe()
        process.executableURL = URL(fileURLWithPath: config.nodeExecutable)
        process.arguments = [root.appendingPathComponent("scripts/menubar-agent.js").path]
        process.currentDirectoryURL = root
        process.environment = ["HOME": NSHomeDirectory(), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "en_US.UTF-8"]
        process.standardInput = stdin
        process.standardOutput = stdout
        process.standardError = FileHandle.nullDevice
        buffer.removeAll()
        child = process; input = stdin; output = stdout
        set(.starting)
        stdout.fileHandleForReading.readabilityHandler = { [weak self, weak process] handle in
            let data = handle.availableData
            if data.isEmpty { handle.readabilityHandler = nil; return }
            Task { @MainActor in
                guard let self, self.child === process else { return }
                self.buffer.append(data)
                while let newline = self.buffer.firstIndex(of: 10) {
                    let line = String(data: self.buffer[..<newline], encoding: .utf8)
                    self.buffer.removeSubrange(...newline)
                    if line == "HIRA_APP_HEALTHY", self.state != .stopping {
                        self.lastHealthy = Date()
                        self.set(.running)
                    }
                }
                if self.buffer.count > 4096 { self.buffer.removeAll() }
            }
        }
        process.terminationHandler = { [weak self] process in
            Task { @MainActor in
                guard let self, self.child === process else { return }
                let expected = self.state == .stopping
                self.output?.fileHandleForReading.readabilityHandler = nil
                try? self.input?.fileHandleForWriting.close()
                self.child = nil; self.input = nil; self.output = nil
                self.set(expected ? .stopped : .failed, expected ? nil : "서버가 종료되었습니다 · 설정 또는 포트 확인")
                self.stopped?()
            }
        }
        do { try process.run() }
        catch {
            stdout.fileHandleForReading.readabilityHandler = nil
            child = nil; input = nil; output = nil
            set(.failed, "Node 실행 실패 · 앱을 다시 빌드하세요")
            return
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 10) { [weak self, weak process] in
            guard let self, self.child === process, self.state == .starting else { return }
            self.stop()
        }
    }

    func stop() {
        guard let process = child else { return }
        guard state != .stopping else { return }
        set(.stopping)
        try? input?.fileHandleForWriting.close()
        DispatchQueue.main.asyncAfter(deadline: .now() + 3) { [weak self, weak process] in
            guard let self, let process, self.child === process, process.isRunning else { return }
            process.terminate()
        }
    }
}

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {
    private var item: NSStatusItem!
    private var timer: Timer?
    private var signals: [DispatchSourceSignal] = []
    private var quitting = false
    private let controller: AgentController

    override init() {
        let url = Bundle.main.url(forResource: "Runtime", withExtension: "json")
        let config = url.flatMap { try? Data(contentsOf: $0) }.flatMap { try? JSONDecoder().decode(RuntimeConfig.self, from: $0) }
        controller = AgentController(config: config)
        super.init()
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        if let id = Bundle.main.bundleIdentifier, NSRunningApplication.runningApplications(withBundleIdentifier: id).count > 1 {
            NSApp.terminate(nil); return
        }
        item = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        controller.changed = { [weak self] in self?.render() }
        controller.stopped = { [weak self] in if self?.quitting == true { NSApp.reply(toApplicationShouldTerminate: true) } }
        render(); controller.refresh()
        timer = Timer.scheduledTimer(withTimeInterval: 2, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.controller.refresh() }
        }
        for sig in [SIGTERM, SIGINT, SIGHUP] {
            signal(sig, SIG_IGN)
            let source = DispatchSource.makeSignalSource(signal: sig, queue: .main)
            source.setEventHandler { NSApp.terminate(nil) }
            source.resume(); signals.append(source)
        }
    }

    private func render() {
        let menu = NSMenu()
        menu.autoenablesItems = false
        let status = NSMenuItem(title: controller.state.rawValue, action: nil, keyEquivalent: "")
        status.isEnabled = false; menu.addItem(status)
        let detail = NSMenuItem(title: controller.detail, action: nil, keyEquivalent: "")
        detail.isEnabled = false; menu.addItem(detail)
        menu.addItem(.separator())
        func command(_ title: String, _ action: Selector, _ enabled: Bool, _ key: String = "") {
            let entry = NSMenuItem(title: title, action: action, keyEquivalent: key)
            entry.target = self; entry.isEnabled = enabled; menu.addItem(entry)
        }
        if controller.ownsProcess {
            let busy = controller.state == .starting || controller.state == .stopping
            command("서버 중지", #selector(stop), !busy)
        } else {
            command("서버 시작", #selector(start), controller.canStart)
        }
        menu.addItem(.separator())
        command("e-Form 열기", #selector(openSite), true)
        command("종료", #selector(quit), true, "q")
        item.menu = menu
        let color: NSColor
        switch controller.state {
        case .running: color = .systemGreen
        case .blocked, .failed: color = .systemRed
        case .stopped, .starting, .stopping: color = .systemGray
        }
        item.button?.image = nil
        item.button?.attributedTitle = NSAttributedString(string: "eF", attributes: [
            .foregroundColor: color,
            .font: NSFont.systemFont(ofSize: 12, weight: .bold)
        ])
        item.button?.toolTip = "HIRA e-Form · \(controller.state.rawValue)"
        item.button?.setAccessibilityLabel("HIRA e-Form, \(controller.state.rawValue)")
    }
    @objc private func start() { controller.start() }
    @objc private func stop() { controller.stop() }
    @objc private func openSite() { NSWorkspace.shared.open(URL(string: "https://ef.hira.or.kr")!) }
    @objc private func quit() { NSApp.terminate(nil) }
    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        guard controller.ownsProcess else { return .terminateNow }
        quitting = true; controller.stop(); return .terminateLater
    }
}

@main
struct HiraApp {
    @MainActor static func main() {
        let application = NSApplication.shared
        application.setActivationPolicy(.accessory)
        let delegate = AppDelegate()
        application.delegate = delegate
        withExtendedLifetime(delegate) { application.run() }
    }
}
