import SwiftUI

struct MatchDetailView: View {
    let match: Match

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Theme.s5) {
                // Teams + ring
                FrostCard(padding: Theme.s4) {
                    VStack(alignment: .leading, spacing: Theme.s3) {
                        // Eyebrow
                        HStack(spacing: Theme.s2) {
                            Eyebrow(text: "MATCHDAY \(match.matchday)")
                            Spacer()
                            CountdownPill(kickoff: match.kickoff)
                        }

                        // Matchup row
                        HStack(alignment: .center) {
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

                        // Tier pill
                        let tier = Format.tierStyle(match.myPick.tier, label: match.myPick.tierLabel)
                        SoftPill(text: tier.text, bg: tier.bg, fg: tier.fg)
                    }
                }

                // Placeholder
                FrostCard(padding: Theme.s4) {
                    VStack(alignment: .leading, spacing: Theme.s3) {
                        Eyebrow(text: "FULL DETAIL")
                        Text("Full detail in Phase 6")
                            .font(.bodyX)
                            .foregroundStyle(Theme.textDim)
                    }
                }
            }
            .padding(.horizontal, Theme.s4)
            .padding(.top, Theme.s6)
            .padding(.bottom, Theme.s8)
        }
        .scrollIndicators(.hidden)
        .background(Theme.bg.ignoresSafeArea())
        .navigationTitle("Matchday \(match.matchday)")
        .navigationBarTitleDisplayMode(.inline)
    }
}
