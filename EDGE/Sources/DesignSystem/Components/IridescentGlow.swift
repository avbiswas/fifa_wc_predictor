import SwiftUI
struct IridescentGlow: View {
    var intensity: Double = 1.0
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0/30.0, paused: reduceMotion)) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            ZStack {
                blob(Theme.iridBlue,  baseX: -70, baseY: -10, t: t, sx: 0.21, sy: 0.17)
                blob(Theme.iridLilac, baseX:  70, baseY: -30, t: t, sx: 0.16, sy: 0.23)
                blob(Theme.iridBlush, baseX: -30, baseY:  40, t: t, sx: 0.13, sy: 0.20)
                blob(Theme.iridPeach, baseX:  60, baseY:  40, t: t, sx: 0.24, sy: 0.14)
                blob(Theme.iridMint,  baseX:   0, baseY:   0, t: t, sx: 0.18, sy: 0.16)
            }
            .blur(radius: 44)
            .opacity(0.85 * intensity)
        }
        .allowsHitTesting(false)
    }
    private func blob(_ c: Color, baseX: CGFloat, baseY: CGFloat, t: Double, sx: Double, sy: Double) -> some View {
        let dx = CGFloat(sin(t * sx)) * 22, dy = CGFloat(cos(t * sy)) * 18
        let s  = 1 + 0.12 * sin(t * (sx + 0.05))
        return Circle().fill(c).frame(width: 170, height: 170)
            .scaleEffect(s).offset(x: baseX + dx, y: baseY + dy)
    }
}
