import SwiftUI

struct MatchDetailView: View {
    let match: Match
    var ns: Namespace.ID? = nil
    @EnvironmentObject var store: AppStore

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Theme.s5) {
                // 1. Hero
                heroSection
                    .generativeAppear(0)

                // 2. Why this pick
                whySection
                    .generativeAppear(1)

                // 3. The matchup
                matchupSection
                    .generativeAppear(2)

                // 4. The room
                roomSection
                    .generativeAppear(3)

                // 5. Other scores
                otherScoresSection
                    .generativeAppear(4)

                // 6. News (if any)
                if !match.news.isEmpty {
                    newsSection
                        .generativeAppear(5)
                }
            }
            .padding(.horizontal, Theme.s4)
            .padding(.top, Theme.s6)
            .padding(.bottom, Theme.s8)
        }
        .scrollIndicators(.hidden)
        .id(store.generation)
        .background {
            ZStack {
                Theme.bg.ignoresSafeArea()
                IridescentGlow(intensity: 0.25).ignoresSafeArea()
            }
        }
        .navigationTitle("Matchday \(match.matchday)")
        .navigationBarTitleDisplayMode(.inline)
        .applyZoomTransition(ns: ns, matchID: match.id)
        .onAppear {
            // Success haptic on "Spot on" result (fires once per appearance)
            if match.myPick.result?.outcome == "exact" {
                UINotificationFeedbackGenerator().notificationOccurred(.success)
            }
        }
    }

    // MARK: - 1. Hero

    @ViewBuilder
    private var heroSection: some View {
        VStack(spacing: Theme.s4) {
            // Teams + ranks
            VStack(alignment: .leading, spacing: Theme.s2) {
                HStack(spacing: Theme.s2) {
                    TeamBadge(code: match.home.code, size: 36)
                    Text(match.home.name)
                        .font(.headlineX)
                        .foregroundStyle(Theme.text)
                    Text("#\(match.home.rank)")
                        .font(.calloutX)
                        .foregroundStyle(Theme.textDim)
                }
                HStack(spacing: Theme.s2) {
                    TeamBadge(code: match.away.code, size: 36)
                    Text(match.away.name)
                        .font(.headlineX)
                        .foregroundStyle(Theme.text)
                    Text("#\(match.away.rank)")
                        .font(.calloutX)
                        .foregroundStyle(Theme.textDim)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            // SoftRing (centered)
            SoftRing(
                value: Format.ringFill(oneIn: match.myPick.exactChanceOneIn),
                color: Format.tierRingColor(match.myPick.tier),
                size: 140
            ) {
                Text(match.myPick.score)
                    .font(.displayX)
                    .monospacedDigit()
            }
            .frame(maxWidth: .infinity)

            // Tier pill + countdown/outcome
            HStack(spacing: Theme.s2) {
                let tier = Format.tierStyle(match.myPick.tier, label: match.myPick.tierLabel)
                SoftPill(text: tier.text, bg: tier.bg, fg: tier.fg)

                Spacer()

                if match.status == "upcoming" {
                    CountdownPill(kickoff: match.kickoff)
                } else if let result = match.myPick.result {
                    let chip = Format.outcomeChip(result.outcome, points: result.points)
                    SoftPill(text: chip.text, bg: chip.bg, fg: chip.fg)
                }
            }

            // Chance line
            Text("\(Format.chanceText(oneIn: match.myPick.exactChanceOneIn)) chance it lands exactly.")
                .font(.bodyX)
                .foregroundStyle(Theme.textDim)
        }
    }

    // MARK: - 2. Why this pick

    @ViewBuilder
    private var whySection: some View {
        FrostCard(padding: Theme.s4) {
            VStack(alignment: .leading, spacing: Theme.s3) {
                Eyebrow(text: "WHY \(match.myPick.score)")

                ForEach(Array(match.myPick.reasons.enumerated()), id: \.offset) { idx, reason in
                    HStack(alignment: .top, spacing: Theme.s2) {
                        Image(systemName: "checkmark")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundStyle(Theme.posText)
                            .padding(.top, 2)
                        Text(reason)
                            .font(.bodyX)
                            .foregroundStyle(Theme.text)
                    }
                    .generativeAppear(idx + 1)
                }
            }
        }
    }

    // MARK: - 3. The matchup

    @ViewBuilder
    private var matchupSection: some View {
        FrostCard(padding: Theme.s4) {
            VStack(alignment: .leading, spacing: Theme.s3) {
                StrengthBar(
                    home: match.odds.home,
                    draw: match.odds.draw,
                    away: match.odds.away,
                    homeCode: match.home.code,
                    awayCode: match.away.code
                )

                Text(Format.strengthWords(match.favoriteStrength))
                    .font(.bodyX)
                    .foregroundStyle(Theme.text)

                if match.upset.isUpset {
                    HStack(spacing: Theme.s1) {
                        Image(systemName: "exclamationmark.triangle")
                            .foregroundStyle(Theme.negText)
                        Text(match.upset.text)
                            .font(.bodyX)
                            .foregroundStyle(Theme.negText)
                    }
                }
            }
        }
    }

    // MARK: - 4. The room

    @ViewBuilder
    private var roomSection: some View {
        FrostCard(padding: Theme.s4) {
            VStack(alignment: .leading, spacing: Theme.s3) {
                Eyebrow(text: "THE ROOM")

                // FriendDots row
                HStack(spacing: 6) {
                    ForEach(0..<match.fieldExposure.friendsTotal, id: \.self) { idx in
                        Circle()
                            .fill(idx < match.fieldExposure.onSamePick
                                  ? AnyShapeStyle(LinearGradient(
                                      colors: [Theme.iridBlue, Theme.iridLilac],
                                      startPoint: .topLeading,
                                      endPoint: .bottomTrailing))
                                  : AnyShapeStyle(Theme.track))
                            .frame(width: 10, height: 10)
                    }
                }

                // Separation sentence
                let onSame = match.fieldExposure.onSamePick
                let total = match.fieldExposure.friendsTotal
                if onSame >= total / 2 {
                    Text("\(onSame) of \(total) friends are here too — safe, low separation.")
                        .font(.bodyX)
                        .foregroundStyle(Theme.text)
                } else {
                    Text("Only \(onSame) of \(total) friends land here — that's your separation.")
                        .font(.bodyX)
                        .foregroundStyle(Theme.text)
                }

                // Chips row
                HStack(spacing: Theme.s2) {
                    let lev = Format.leverageChip(match.myPick.leverage)
                    SoftPill(text: lev.text, bg: lev.bg, fg: lev.fg, systemImage: lev.icon)

                    let leader = Format.leaderChip(match.myPick.vsLeader, leaderName: store.feed?.me.leaderName ?? "")
                    SoftPill(text: leader.text, bg: leader.bg, fg: leader.fg)
                }

                // Leader tip
                if let leaderPick = match.fieldExposure.leaderPick {
                    Text("Leader's likely tip: \(leaderPick)")
                        .font(.calloutX)
                        .foregroundStyle(Theme.textDim)
                }
            }
        }
    }

    // MARK: - 5. Other scores

    @ViewBuilder
    private var otherScoresSection: some View {
        FrostCard(padding: Theme.s4) {
            VStack(alignment: .leading, spacing: Theme.s3) {
                Eyebrow(text: "OTHER SCORES")

                let maxEP = match.alternates.map(\.expectedPoints).max() ?? 1

                ForEach(match.alternates) { alt in
                    HStack(spacing: Theme.s2) {
                        Text(alt.score)
                            .font(.headlineX)
                            .monospacedDigit()
                            .foregroundStyle(Theme.text)

                        // Thin iridescent bar (relative length, no number shown)
                        GeometryReader { geo in
                            Capsule()
                                .fill(LinearGradient(
                                    colors: [Theme.iridBlue, Theme.iridLilac],
                                    startPoint: .leading,
                                    endPoint: .trailing))
                                .frame(width: max(4, geo.size.width * (alt.expectedPoints / maxEP)))
                        }
                        .frame(height: 4)

                        Text(alt.note)
                            .font(.calloutX)
                            .foregroundStyle(Theme.textDim)

                        if alt.score == match.myPick.score {
                            SoftPill(text: "Your pick", bg: Theme.posBG, fg: Theme.posText)
                        }
                    }
                }
            }
        }
    }

    // MARK: - 6. News

    @ViewBuilder
    private var newsSection: some View {
        FrostCard(padding: Theme.s4) {
            VStack(alignment: .leading, spacing: Theme.s3) {
                Eyebrow(text: "NEWS")

                ForEach(Array(match.news.enumerated()), id: \.offset) { _, item in
                    HStack(alignment: .top, spacing: Theme.s2) {
                        Image(systemName: "newspaper")
                            .font(.bodyX)
                            .foregroundStyle(Theme.textDim)
                            .padding(.top, 2)
                        Text(item)
                            .font(.bodyX)
                            .foregroundStyle(Theme.text)
                    }
                }
            }
        }
    }
}

// MARK: - Zoom Transition Helper

extension View {
    @ViewBuilder
    func applyZoomTransition(ns: Namespace.ID?, matchID: String) -> some View {
        if let ns {
            self.navigationTransition(.zoom(sourceID: matchID, in: ns))
        } else {
            self
        }
    }
}
