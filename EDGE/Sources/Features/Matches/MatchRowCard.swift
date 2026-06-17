import SwiftUI

struct MatchRowCard: View {
    let match: Match

    var body: some View {
        FrostCard(padding: Theme.s4) {
            VStack(alignment: .leading, spacing: Theme.s3) {
                if match.status == "upcoming" {
                    upcomingContent
                } else {
                    finalContent
                }
            }
        }
    }

    // MARK: - Upcoming Variant

    @ViewBuilder
    private var upcomingContent: some View {
        // Row 1: CountdownPill + tier pill
        HStack(spacing: Theme.s2) {
            CountdownPill(kickoff: match.kickoff)
            Spacer()
            let tier = Format.tierStyle(match.myPick.tier, label: match.myPick.tierLabel)
            SoftPill(text: tier.text, bg: tier.bg, fg: tier.fg)
        }

        // Row 2: Home team + SoftRing
        HStack(alignment: .center) {
            VStack(alignment: .leading, spacing: Theme.s2) {
                HStack(spacing: Theme.s2) {
                    TeamBadge(code: match.home.code, size: 42)
                    Text(match.home.name)
                        .font(.headlineX)
                        .foregroundStyle(Theme.text)
                }
                HStack(spacing: Theme.s2) {
                    TeamBadge(code: match.away.code, size: 42)
                    Text(match.away.name)
                        .font(.headlineX)
                        .foregroundStyle(Theme.text)
                }
            }
            Spacer()
            SoftRing(
                value: Format.ringFill(oneIn: match.myPick.exactChanceOneIn),
                color: Format.tierRingColor(match.myPick.tier),
                size: 88
            ) {
                Text(match.myPick.score)
                    .font(.displayX)
                    .monospacedDigit()
            }
        }

        // Row 4: Strength bar
        StrengthBar(
            home: match.odds.home,
            draw: match.odds.draw,
            away: match.odds.away,
            homeCode: match.home.code,
            awayCode: match.away.code
        )
    }

    // MARK: - Final Variant

    @ViewBuilder
    private var finalContent: some View {
        // Row 1: Eyebrow + outcome chip
        HStack(spacing: Theme.s2) {
            Eyebrow(text: "Matchday \(match.matchday) · \(formatDate(match.kickoff))")
            Spacer()
            if let result = match.myPick.result {
                let chip = Format.outcomeChip(result.outcome, points: result.points)
                SoftPill(text: chip.text, bg: chip.bg, fg: chip.fg)
            }
        }

        // Row 2: Home team + actual score
        HStack(spacing: Theme.s2) {
            TeamBadge(code: match.home.code, size: 36)
            Text(match.home.name)
                .font(.headlineX)
                .foregroundStyle(Theme.text)
            Spacer()
            if let res = match.result {
                Text("\(res.home)")
                    .font(.displayX)
                    .monospacedDigit()
                    .foregroundStyle(scoreColor)
            }
        }

        // Row 3: Away team + actual score
        HStack(spacing: Theme.s2) {
            TeamBadge(code: match.away.code, size: 36)
            Text(match.away.name)
                .font(.headlineX)
                .foregroundStyle(Theme.text)
            Spacer()
            if let res = match.result {
                Text("\(res.away)")
                    .font(.displayX)
                    .monospacedDigit()
                    .foregroundStyle(scoreColor)
            }
        }

        // Row 4: "your tip" + check/x
        HStack(spacing: Theme.s2) {
            Text("your tip \(match.myPick.score)")
                .font(.calloutX)
                .foregroundStyle(Theme.textDim)
                .monospacedDigit()
            Spacer()
            if let result = match.myPick.result {
                Image(systemName: result.outcome == "miss" ? "xmark" : "checkmark")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(result.outcome == "miss" ? Theme.negText : Theme.posText)
            }
        }
    }

    // MARK: - Helpers

    private var scoreColor: Color {
        guard let result = match.myPick.result else { return Theme.text }
        return result.outcome == "miss" ? Theme.negText : Theme.posText
    }

    private func formatDate(_ date: Date) -> String {
        let f = DateFormatter()
        f.dateFormat = "d MMM"
        return f.string(from: date)
    }
}
