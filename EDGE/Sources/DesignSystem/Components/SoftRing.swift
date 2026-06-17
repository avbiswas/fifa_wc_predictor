import SwiftUI
struct SoftRing<Center: View>: View {
    var value: Double                 // 0...1
    var color: Color
    var lineWidth: CGFloat = 8
    var size: CGFloat = 108
    var a11yLabel: String? = nil
    @ViewBuilder var center: Center
    @State private var animated: Double = 0
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    var body: some View {
        ZStack {
            Circle().stroke(Theme.track, lineWidth: lineWidth)
            Circle().trim(from: 0, to: animated)
                .stroke(color.opacity(0.9), style: StrokeStyle(lineWidth: lineWidth, lineCap: .round))
                .rotationEffect(.degrees(-90))
                .shadow(color: color.opacity(0.25), radius: 6)     // soft, not neon
            center
        }
        .frame(width: size, height: size)
        .modifier(A11yRingLabel(label: a11yLabel))
        .onAppear {
            let v = max(0, min(1, value))
            if reduceMotion { animated = v; return }
            withAnimation(.spring(response: 1.0, dampingFraction: 0.9).delay(0.25)) { animated = v }
        }
    }
}

// MARK: - Accessibility modifier

private struct A11yRingLabel: ViewModifier {
    let label: String?
    func body(content: Content) -> some View {
        if let label {
            content
                .accessibilityElement(children: .ignore)
                .accessibilityLabel(label)
        } else {
            content
        }
    }
}
