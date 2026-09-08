import Foundation
import Security
import Darwin

// Only this item's metadata is exposed. There is deliberately no print/get command.
let identity: [String: Any] = [
    kSecClass as String: kSecClassGenericPassword,
    kSecAttrService as String: "hira-eform-macos.certificate-password",
    kSecAttrAccount as String: "local-certificate",
]

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

func readSecret(_ prompt: String) -> Data {
    guard isatty(STDIN_FILENO) == 1 else {
        fail("Run setup directly in your own terminal; piped input is refused.")
    }
    guard let pointer = getpass(prompt) else { fail("Password entry cancelled.") }
    let count = strlen(pointer)
    defer { memset(pointer, 0, count) }
    guard count > 0 else { fail("Empty password refused.") }
    return Data(bytes: pointer, count: count)
}

guard CommandLine.arguments.count == 2 else { fail("Usage: certificate-secret set|status") }
switch CommandLine.arguments[1] {
case "set":
    var first = readSecret("Certificate password (hidden): ")
    var second = readSecret("Confirm password (hidden): ")
    defer {
        first.resetBytes(in: 0..<first.count)
        second.resetBytes(in: 0..<second.count)
    }
    guard first == second else { fail("Passwords do not match; nothing was saved.") }
    var item = identity
    item[kSecValueData as String] = first
    item[kSecAttrLabel as String] = "HIRA e-Form certificate password"
    let added = SecItemAdd(item as CFDictionary, nil)
    let result = added == errSecDuplicateItem
        ? SecItemUpdate(identity as CFDictionary, [kSecValueData as String: first] as CFDictionary)
        : added
    guard result == errSecSuccess else { fail("Keychain write failed (OSStatus \(result)).") }
    print("Certificate password saved to macOS Keychain. No password was printed.")
case "status":
    var query = identity
    query[kSecReturnAttributes as String] = true
    query[kSecMatchLimit as String] = kSecMatchLimitOne
    var attributes: CFTypeRef?
    let result = SecItemCopyMatching(query as CFDictionary, &attributes)
    if result == errSecItemNotFound {
        print("Certificate password: not configured")
        exit(2)
    }
    guard result == errSecSuccess else { fail("Keychain check failed (OSStatus \(result)).") }
    print("Certificate password: configured (value not read)")
default:
    fail("Usage: certificate-secret set|status")
}
