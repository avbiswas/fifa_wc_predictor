import SwiftUI

struct CountdownPill: View {
    let kickoff: Date
    @State private var now = Date()

    private var isPast: Bool { kickoff <= now }

    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(isPast ? Theme.warnText : Theme.spark)
                .frame(width: 5, height: 5)

            Text(Format.countdown(to: kickoff))
                .font(.calloutX)
                .monospacedDigit()
                .foregroundStyle(isPast ? Theme.warnText : Theme.actText)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(Capsule().fill(isPast ? Theme.warnBG : Theme.actBG))
        .background(Capsule().fill(.ultraThinMaterial))
        .overlay(Capsule().strokeBorder(Theme.hairline, lineWidth: 1))
        .onReceive(Timer.publish(every: 60, on: .main, in: .common).autoconnect()) { date in
            now = date
        }
    }
}
