import SwiftUI
struct GeneratedStatus: View {
    let updatedAt: Date
    var generating: Bool = false
    @State private var pulse = false
    var body: some View {
        HStack(spacing: 6) {
            Circle().fill(Theme.spark).frame(width: 7, height: 7)
                .scaleEffect(pulse ? 1.2 : 0.8).opacity(pulse ? 1 : 0.5)
                .onAppear { withAnimation(.easeInOut(duration: 1.2).repeatForever(autoreverses: true)) { pulse = true } }
            Text(generating ? "Generating your briefing…" : "Generated \(Format.relativeUpdated(updatedAt))")
                .font(.calloutX).foregroundStyle(Theme.textDim)
        }
    }
}
