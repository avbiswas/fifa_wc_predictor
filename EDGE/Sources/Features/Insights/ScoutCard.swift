import SwiftUI

struct ScoutCard: View {
    let report: ScoutReport

    var body: some View {
        FrostCard {
            VStack(alignment: .leading, spacing: Theme.s3) {
                // Header
                HStack(spacing: Theme.s1) {
                    if report.isLeader {
                        Image(systemName: "crown.fill")
                            .font(.calloutX)
                            .foregroundStyle(Theme.actText)
                    }
                    Text(report.name)
                        .font(.headlineX)
                        .foregroundStyle(Theme.text)
                    Spacer()
                    Text("#\(report.rank) · \(report.points) pts")
                        .font(.calloutX)
                        .monospacedDigit()
                        .foregroundStyle(Theme.textDim)
                }

                // Tag pill
                SoftPill(
                    text: report.tag,
                    bg: tagBackground,
                    fg: tagForeground
                )

                // Blurb
                Text(report.blurb)
                    .font(.bodyX)
                    .foregroundStyle(Theme.text)

                // Divider
                Rectangle()
                    .fill(Theme.track)
                    .frame(height: 1)

                // Trait bars
                ForEach(report.traits) { trait in
                    HStack(spacing: Theme.s2) {
                        Eyebrow(text: trait.label)
                            .frame(width: 70, alignment: .leading)
                        TraitLevelBar(level: trait.level)
                        Text(trait.value)
                            .font(.calloutX)
                            .foregroundStyle(Theme.textDim)
                    }
                }
            }
        }
    }

    // MARK: - Tag color logic

    private var tagBackground: Color {
        let lower = report.tag.lowercased()
        if lower.contains("chaos") {
            return Theme.warnBG
        } else if lower.contains("contrarian") || lower.contains("away") {
            return Theme.actBG
        }
        return Color(hex: "F0F0F3")
    }

    private var tagForeground: Color {
        let lower = report.tag.lowercased()
        if lower.contains("chaos") {
            return Theme.warnText
        } else if lower.contains("contrarian") || lower.contains("away") {
            return Theme.actText
        }
        return Theme.textDim
    }
}

// MARK: - TraitLevelBar

private struct TraitLevelBar: View {
    let level: Int
    @State private var shown = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        HStack(spacing: 3) {
            ForEach(0..<3, id: \.self) { index in
                Capsule()
                    .fill(index < level ? Theme.iridLilac : Theme.track)
                    .frame(width: shown ? 18 : 0, height: 7)
            }
        }
        .onAppear {
            if reduceMotion {
                shown = true
                return
            }
            withAnimation(.easeOut(duration: 0.6).delay(0.15)) {
                shown = true
            }
        }
    }
}
