import SwiftUI

struct TodayView: View {
    @EnvironmentObject var store: AppStore

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()
            IridescentGlow(intensity: 1.0).ignoresSafeArea()

            if let feed = store.feed {
                ScrollView {
                    VStack(alignment: .leading, spacing: Theme.s5) {
                        // 0. Generated status
                        GeneratedStatus(updatedAt: feed.updatedAt, generating: false)
                            .generativeAppear(0)

                        // 1. Date label
                        Text(feed.updatedAt, format: .dateTime.weekday().day().month())
                            .font(.calloutX)
                            .foregroundStyle(Theme.textDim)
                            .generativeAppear(1)

                        // 2. Greeting — word-by-word build
                        greetingWords(feed.me.name)
                            .generativeAppear(2)

                        // 3. Standing card
                        standingCard(feed.me)
                            .generativeAppear(3)

                        // 4. Tonight's plan card
                        planCard(feed.strategy)
                            .generativeAppear(4)
                    }
                    .padding(.horizontal, Theme.s4)
                    .padding(.top, Theme.s6)
                    .padding(.bottom, 100)
                }
                .scrollIndicators(.hidden)
                .id(store.generation)
                .refreshable { await store.refresh() }
            } else {
                // Loading state
                VStack(spacing: Theme.s4) {
                    ProgressView()
                    Text("Loading your briefing…")
                        .font(.bodyX)
                        .foregroundStyle(Theme.textDim)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }

    // MARK: - Greeting (word-by-word build)

    @ViewBuilder
    private func greetingWords(_ name: String) -> some View {
        let greeting = Format.greeting(name)
        let words = greeting.split(separator: " ").map(String.init)
        HStack(spacing: 0) {
            ForEach(Array(words.enumerated()), id: \.offset) { index, word in
                Text(word + (index < words.count - 1 ? " " : ""))
                    .font(index == words.count - 1 ? .greeting.weight(.medium) : .greeting)
                    .foregroundStyle(Theme.text)
            }
        }
    }

    // MARK: - Standing Card

    @ViewBuilder
    private func standingCard(_ me: Me) -> some View {
        FrostCard(padding: Theme.s4) {
            VStack(alignment: .leading, spacing: Theme.s3) {
                // Eyebrow + orb
                HStack(spacing: Theme.s2) {
                    Eyebrow(text: "YOUR POSITION")
                    Spacer()
                    Circle()
                        .fill(LinearGradient(
                            colors: [Theme.iridBlue, Theme.iridLilac],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ))
                        .frame(width: 12, height: 12)
                }

                // Rank line
                HStack(alignment: .firstTextBaseline, spacing: Theme.s1) {
                    Text("#\(me.rank)")
                        .font(.heroLight)
                        .monospacedDigit()
                        .foregroundStyle(Theme.text)
                    Text("of \(me.playersCount)")
                        .font(.bodyX)
                        .foregroundStyle(Theme.textDim)
                }

                // Deficit line
                if me.rank == 1 || me.deficit == 0 {
                    Text("You're top.")
                        .font(.bodyX)
                        .foregroundStyle(Theme.posText)
                } else {
                    Text("\(me.deficit) points behind \(me.leaderName)")
                        .font(.bodyX)
                        .foregroundStyle(Theme.text)
                }

                // Gap rail
                GapRail(
                    mine: me.points,
                    leader: me.leaderPoints,
                    leaderName: me.leaderName
                )

                // Tiebreaker pill
                SoftPill(
                    text: "ties: \(me.tiebreaker)",
                    bg: Theme.actBG,
                    fg: Theme.actText
                )
            }
        }
    }

    // MARK: - Tonight's Plan Card

    @ViewBuilder
    private func planCard(_ strategy: Strategy) -> some View {
        FrostCard(padding: Theme.s4) {
            VStack(alignment: .leading, spacing: Theme.s3) {
                // Eyebrow + mode icon
                HStack(spacing: Theme.s2) {
                    Eyebrow(text: "TONIGHT'S PLAN")
                    Spacer()
                    Image(systemName: Format.modeIcon(strategy.mode))
                        .font(.calloutX)
                        .foregroundStyle(Theme.textDim)
                }

                // Headline
                Text(strategy.headline)
                    .font(.titleX)
                    .foregroundStyle(Theme.ink)

                // Subtitle
                Text(strategy.subtitle)
                    .font(.bodyX)
                    .foregroundStyle(Theme.textDim)

                // Divider
                Rectangle()
                    .fill(Theme.track)
                    .frame(height: 1)

                // Draw plan row
                HStack(spacing: Theme.s2) {
                    Image(systemName: "circle.lefthalf.filled")
                        .font(.calloutX)
                        .foregroundStyle(Theme.textDim)
                    Text("\(strategy.drawPlan.planned) draws planned")
                        .font(.bodyX)
                        .foregroundStyle(Theme.text)
                    Text("·")
                        .foregroundStyle(Theme.textMute)
                    Text(strategy.drawPlan.reason)
                        .font(.calloutX)
                        .foregroundStyle(Theme.textDim)
                }
            }
        }
    }
}
