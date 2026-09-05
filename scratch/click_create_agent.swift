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

// 1. Close current error tab (Cmd + W, keycode 13)
sendKey(keyCode: 13, flags: .maskCommand)
Thread.sleep(forTimeInterval: 0.5)

// 2. Select Tab 2 (Cmd + 2, keycode 19)
sendKey(keyCode: 19, flags: .maskCommand)
Thread.sleep(forTimeInterval: 1.0)

// 3. Click "+ Create agent" button at approx (760, 240)
let btnPoint = CGPoint(x: 760, y: 240)
if let down = CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: btnPoint, mouseButton: .left),
   let up = CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: btnPoint, mouseButton: .left) {
    down.post(tap: .cghidEventTap)
    Thread.sleep(forTimeInterval: 0.1)
    up.post(tap: .cghidEventTap)
    print("Clicked + Create agent at \(btnPoint)")
}

Thread.sleep(forTimeInterval: 5.0)

// 4. Capture screenshot
let task = Process()
task.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
task.arguments = ["-l", "9037", "-x", "scratch/screenshots_gcp_console/07_gcp_console_agent_creation_modal.png"]
try? task.run()
task.waitUntilExit()
print("Captured creation modal")
