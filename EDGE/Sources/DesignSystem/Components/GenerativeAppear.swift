import SwiftUI
struct GenerativeAppear: ViewModifier {
    let index: Int
    var base: Double = 0.12
    var step: Double = 0.085
    @State private var shown = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    func body(content: Content) -> some View {
        content
            .opacity(shown ? 1 : 0)
            .blur(radius: shown ? 0 : 9)
            .scaleEffect(shown ? 1 : 0.97, anchor: .center)
            .offset(y: shown ? 0 : 16)
            .onAppear {
                if reduceMotion { shown = true; return }
                withAnimation(.spring(response: 0.75, dampingFraction: 0.82)
                    .delay(base + Double(index) * step)) { shown = true }
            }
    }
}
extension View {
    /// Apply down a screen with an incrementing index: .generativeAppear(0), .generativeAppear(1)…
    func generativeAppear(_ index: Int) -> some View { modifier(GenerativeAppear(index: index)) }
}
