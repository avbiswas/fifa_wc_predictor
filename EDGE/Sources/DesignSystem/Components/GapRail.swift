import SwiftUI
struct GapRail: View {
    let mine: Int, leader: Int          // 18, 24
    let leaderName: String
    @State private var p: CGFloat = 0
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    private var frac: CGFloat { leader <= 0 ? 0 : CGFloat(mine)/CGFloat(leader) }
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule().fill(Theme.track).frame(height: 6)
                    Capsule().fill(LinearGradient(colors: [Theme.iridBlue, Theme.iridLilac],
                                   startPoint: .leading, endPoint: .trailing))
                        .frame(width: geo.size.width * p, height: 6)
                    Circle().fill(.white).frame(width: 14, height: 14)
                        .overlay(Circle().strokeBorder(Theme.spark, lineWidth: 2))
                        .shadow(color: Theme.shadow.opacity(0.18), radius: 3, y: 1)
                        .offset(x: geo.size.width * p - 7)
                }
            }.frame(height: 16)
            HStack {
                Text("\(mine) you").font(.calloutX).foregroundStyle(Theme.text)
                Spacer()
                Text("\(leader) \(leaderName)").font(.calloutX).foregroundStyle(Theme.textDim)
            }.monospacedDigit()
        }
        .onAppear {
            if reduceMotion { p = frac; return }
            withAnimation(.spring(response: 1.0, dampingFraction: 0.9).delay(0.3)) { p = frac }
        }
    }
}
