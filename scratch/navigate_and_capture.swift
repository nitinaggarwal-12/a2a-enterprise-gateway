import CoreGraphics
import Foundation
import AppKit

func sendKey(keyCode: CGKeyCode, flags: CGEventFlags = []) {
    let src = CGEventSource(stateID: .hidSystemState)
    if let down = CGEvent(keyboardEventSource: src, virtualKey: keyCode, keyDown: true),
       let up = CGEvent(keyboardEventSource: src, virtualKey: keyCode, keyDown: false) {
        down.flags = flags
        up.flags = flags
        down.post(tap: .cghidEventTap)
        Thread.sleep(forTimeInterval: 0.05)
        up.post(tap: .cghidEventTap)
    }
}

guard CommandLine.arguments.count >= 3 else {
    print("Usage: navigate_and_capture <URL> <output_path> [settle_seconds]")
    exit(1)
}

let targetURL = CommandLine.arguments[1]
let outputPath = CommandLine.arguments[2]
let settleSeconds = CommandLine.arguments.count >= 4 ? Double(CommandLine.arguments[3]) ?? 8.0 : 8.0

// 1. Activate Chrome
if let app = NSRunningApplication.runningApplications(withBundleIdentifier: "com.google.Chrome").first {
    app.activate(options: .activateIgnoringOtherApps)
}
Thread.sleep(forTimeInterval: 0.3)

// 2. Click in the window body to ensure focus
let bodyPoint = CGPoint(x: 600, y: 300)
if let down = CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: bodyPoint, mouseButton: .left),
   let up = CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: bodyPoint, mouseButton: .left) {
    down.post(tap: .cghidEventTap)
    Thread.sleep(forTimeInterval: 0.05)
    up.post(tap: .cghidEventTap)
}
Thread.sleep(forTimeInterval: 0.3)

// 3. Open new tab (Cmd + T, keycode 17)
sendKey(keyCode: 17, flags: .maskCommand)
Thread.sleep(forTimeInterval: 0.5)

// 4. Set clipboard to targetURL
let pasteboard = NSPasteboard.general
pasteboard.clearContents()
pasteboard.setString(targetURL, forType: .string)

// 5. Paste URL (Cmd + V, keycode 9)
sendKey(keyCode: 9, flags: .maskCommand)
Thread.sleep(forTimeInterval: 0.2)

// 6. Press Return (keycode 36)
sendKey(keyCode: 36)
print("Navigating to \(targetURL)... waiting \(settleSeconds)s")

// 7. Wait for page load and settling
Thread.sleep(forTimeInterval: settleSeconds)

// 8. Capture Window 9037 using screencapture CLI
let task = Process()
task.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
task.arguments = ["-l", "9037", "-x", outputPath]
try? task.run()
task.waitUntilExit()

print("Screenshot captured to \(outputPath)")
