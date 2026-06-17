import SwiftUI
struct StrengthBar: View {
    let home: Double, draw: Double, away: Double
    let homeCode: String, awayCode: String
    @State private var shown = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    var body: some View {
        VStack(alignment: .leading, spacing: Theme.s2) {
            GeometryReader { geo in
                HStack(spacing: 3) {
                    seg(home, Color(hex: "9DBBA9"), geo.size.width)   // soft sage (home)
                    seg(draw, Theme.textMute,       geo.size.width)   // gray (draw)
                    seg(away, Color(hex: "A9C2E6"), geo.size.width)   // soft blue (away)
                }
            }.frame(height: 8)
            HStack { Text(homeCode); Spacer(); Text("draw"); Spacer(); Text(awayCode) }
                .font(.eyebrowX).foregroundStyle(Theme.textDim)
        }
        .onAppear {
            if reduceMotion { shown = true; return }
            withAnimation(.easeOut(duration: 0.8).delay(0.2)) { shown = true }
        }
    }
    private func seg(_ p: Double, _ c: Color, _ total: CGFloat) -> some View {
        Capsule().fill(c).frame(width: shown ? max(4, total * p) : 0)
    }
}
