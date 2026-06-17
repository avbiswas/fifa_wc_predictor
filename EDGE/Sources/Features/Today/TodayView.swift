import SwiftUI

struct TodayView: View {
    @EnvironmentObject var store: AppStore

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()
            IridescentGlow(intensity: 1.0).ignoresSafeArea()

            if let feed = store.feed {
                NavigationStack {
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

                            // 5. Next match spotlight
                            let upcoming = feed.matches
                                .filter { $0.status == "upcoming" }
                                .sorted { $0.kickoff < $1.kickoff }
                            if let next = upcoming.first {
                                spotlightCard(next)
                                    .generativeAppear(5)
                            }

                            // 6+. Today's other picks
                            if upcoming.count > 1 {
                                otherPicksSection(Array(upcoming.dropFirst()))
                            }

                            // Empty state
                            if upcoming.isEmpty {
                                emptyStateCard
                                    .generativeAppear(5)
                            }
                        }
                        .padding(.horizontal, Theme.s4)
                        .padding(.top, Theme.s6)
                        .padding(.bottom, 100)
                    }
                    .scrollIndicators(.hidden)
                    .id(store.generation)
                    .refreshable { await store.refresh() }
                    .navigationDestination(for: String.self) { id in
                        if let m = feed.matches.first(where: { $0.id == id }) {
                            MatchDetailView(match: m)
                        }
                    }
                }
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

    // MARK: - Next Match Spotlight

    @ViewBuilder
    private func spotlightCard(_ match: Match) -> some View {
        NavigationLink(value: match.id) {
            FrostCard(padding: Theme.s4) {
                VStack(alignment: .leading, spacing: Theme.s3) {
                    // Eyebrow row: NEXT UP · 17:00 · CountdownPill
                    HStack(spacing: Theme.s1) {
                        Eyebrow(text: "NEXT UP")
                        Text("·")
                            .font(.eyebrowX)
                            .foregroundStyle(Theme.textMute)
                        Text(Format.kickoffClock(match.kickoff))
                            .font(.eyebrowX)
                            .foregroundStyle(Theme.textDim)
                        Text("·")
                            .font(.eyebrowX)
                            .foregroundStyle(Theme.textMute)
                        CountdownPill(kickoff: match.kickoff)
                        Spacer()
                    }

                    // Matchup row: teams + SoftRing
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

                    // Strength bar
                    StrengthBar(
                        home: match.odds.home,
                        draw: match.odds.draw,
                        away: match.odds.away,
                        homeCode: match.home.code,
                        awayCode: match.away.code
                    )

                    // Pills row: tier + leverage
                    HStack(spacing: Theme.s2) {
                        let tier = Format.tierStyle(match.myPick.tier, label: match.myPick.tierLabel)
                        SoftPill(text: tier.text, bg: tier.bg, fg: tier.fg)
                        let lev = Format.leverageChip(match.myPick.leverage)
                        SoftPill(text: lev.text, bg: lev.bg, fg: lev.fg, systemImage: lev.icon)
                    }

                    // Ink-pill label: "Why this pick →"
                    HStack(spacing: 8) {
                        Text("Why this pick")
                            .font(.headlineX)
                            .foregroundStyle(.white)
                        Image(systemName: "arrow.right")
                            .font(.system(size: 12, weight: .bold))
                            .foregroundStyle(Theme.ink)
                            .frame(width: 22, height: 22)
                            .background(Circle().fill(.white))
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 13)
                    .background(Capsule().fill(Theme.ink))
                }
            }
        }
        .buttonStyle(PressScale())
    }

    // MARK: - Today's Other Picks

    @ViewBuilder
    private func otherPicksSection(_ matches: [Match]) -> some View {
        VStack(alignment: .leading, spacing: Theme.s2) {
            Eyebrow(text: "TODAY'S PICKS")
                .generativeAppear(6)

            ForEach(Array(matches.enumerated()), id: \.element.id) { index, m in
                NavigationLink(value: m.id) {
                    HStack(spacing: Theme.s3) {
                        TeamBadge(code: m.home.code, size: 32)
                        Text(m.home.code)
                            .font(.calloutX)
                            .foregroundStyle(Theme.text)
                        Text(m.myPick.score)
                            .font(.headlineX)
                            .monospacedDigit()
                            .foregroundStyle(Theme.text)
                        Text(m.away.code)
                            .font(.calloutX)
                            .foregroundStyle(Theme.text)
                        TeamBadge(code: m.away.code, size: 32)
                        Spacer()
                        Circle()
                            .fill(Format.tierRingColor(m.myPick.tier))
                            .frame(width: 8, height: 8)
                    }
                    .padding(.vertical, Theme.s2)
                }
                .buttonStyle(PressScale())
                .generativeAppear(7 + index)
            }
        }
    }

    // MARK: - Empty State

    @ViewBuilder
    private var emptyStateCard: some View {
        FrostCard(padding: Theme.s4) {
            VStack(spacing: Theme.s4) {
                Image(systemName: "calendar")
                    .font(.system(size: 40))
                    .foregroundStyle(Theme.textMute)
                Text("No matches today")
                    .font(.titleX)
                    .foregroundStyle(Theme.text)
                Text("Next up soon")
                    .font(.bodyX)
                    .foregroundStyle(Theme.textDim)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, Theme.s8)
        }
    }
}
