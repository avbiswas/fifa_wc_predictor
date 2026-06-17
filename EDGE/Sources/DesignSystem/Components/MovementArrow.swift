import SwiftUI
struct MovementArrow: View {
    let move: Int
    var body: some View {
        let (icon, color): (String, Color) =
            move > 0 ? ("arrow.up.right", Theme.posText) :
            move < 0 ? ("arrow.down.right", Theme.negText) : ("minus", Theme.textMute)
        return HStack(spacing: 2) {
            Image(systemName: icon).font(.system(size: 10, weight: .semibold))
            if move != 0 { Text("\(abs(move))").font(.eyebrowX).monospacedDigit() }
        }
        .foregroundStyle(color)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(move > 0 ? "Up \(abs(move))" : move < 0 ? "Down \(abs(move))" : "No change")
    }
}
