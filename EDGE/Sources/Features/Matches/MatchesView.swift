import SwiftUI

struct MatchesView: View {
    @EnvironmentObject var store: AppStore
    @State private var showResults = false
    @Namespace private var ns

    private enum Seg: String, CaseIterable {
        case upcoming = "Upcoming"
        case results = "Results"
    }

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()
            IridescentGlow(intensity: 0.35).ignoresSafeArea()

            if let feed = store.feed {
                ScrollView {
                    VStack(alignment: .leading, spacing: Theme.s5) {
                        // Title
                        Text("Matches")
                            .font(.titleX)
                            .foregroundStyle(Theme.ink)
                            .generativeAppear(0)

                        // Segmented control
                        segmentedControl
                            .generativeAppear(1)

                        // Matchday sections
                        let matches = showResults ? resultsMatches(feed.matches) : upcomingMatches(feed.matches)
                        let grouped = groupByMatchday(matches)

                        if grouped.isEmpty {
                            emptyState
                                .generativeAppear(2)
                        } else {
                            var animIndex = 2
                            ForEach(grouped, id: \.matchday) { group in
                                // Section header
                                Eyebrow(text: "MATCHDAY \(group.matchday) · \(formatMatchdayDate(group.matches.first?.kickoff))")
                                    .generativeAppear(animIndex)
                                animIndex += 1

                                // Match cards
                                ForEach(group.matches) { match in
                                    NavigationLink(value: match.id) {
                                        MatchRowCard(match: match)
                                    }
                                    .matchedTransitionSource(id: match.id, in: ns)
                                    .buttonStyle(PressScale())
                                    .generativeAppear(animIndex)
                                    animIndex += 1
                                }
                            }
                        }
                    }
                    .padding(.horizontal, Theme.s4)
                    .padding(.top, Theme.s6)
                    .padding(.bottom, 100)
                }
                .scrollIndicators(.hidden)
                .id(store.generation)
                .refreshable {
                    await store.refresh()
                }
                .navigationDestination(for: String.self) { id in
                    if let m = feed.matches.first(where: { $0.id == id }) {
                        MatchDetailView(match: m, ns: ns)
                    }
                }
            } else {
                // Loading state
                VStack(spacing: Theme.s4) {
                    ProgressView()
                    Text("Loading your matches…")
                        .font(.bodyX)
                        .foregroundStyle(Theme.textDim)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }

    // MARK: - Segmented Control

    @ViewBuilder
    private var segmentedControl: some View {
        HStack(spacing: 0) {
            segButton("Upcoming", selected: !showResults) {
                showResults = false
                UIImpactFeedbackGenerator(style: .light).impactOccurred()
            }
            segButton("Results", selected: showResults) {
                showResults = true
                UIImpactFeedbackGenerator(style: .light).impactOccurred()
            }
        }
        .padding(3)
        .background(Capsule().fill(.ultraThinMaterial))
        .background(Capsule().fill(Theme.card))
        .overlay(Capsule().strokeBorder(Theme.hairline, lineWidth: 1))
        .shadow(color: Theme.shadow.opacity(0.08), radius: 12, x: 0, y: 6)
    }

    @ViewBuilder
    private func segButton(_ title: String, selected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title)
                .font(selected ? .headlineX : .calloutX)
                .foregroundStyle(selected ? .white : Theme.textDim)
                .padding(.horizontal, Theme.s4)
                .padding(.vertical, Theme.s2)
                .background(
                    Capsule()
                        .fill(selected ? Theme.ink : .clear)
                )
        }
        .buttonStyle(.plain)
    }

    // MARK: - Data Helpers

    private func upcomingMatches(_ matches: [Match]) -> [Match] {
        matches
            .filter { $0.status == "upcoming" }
            .sorted { $0.kickoff < $1.kickoff }
    }

    private func resultsMatches(_ matches: [Match]) -> [Match] {
        matches
            .filter { $0.status == "final" }
            .sorted { $0.matchday > $1.matchday }
    }

    private struct MatchdayGroup: Identifiable {
        let matchday: Int
        let matches: [Match]
        var id: Int { matchday }
    }

    private func groupByMatchday(_ matches: [Match]) -> [MatchdayGroup] {
        let grouped = Dictionary(grouping: matches) { $0.matchday }
        return grouped
            .map { MatchdayGroup(matchday: $0.key, matches: $0.value) }
            .sorted { $0.matchday > $1.matchday }
    }

    private func formatMatchdayDate(_ date: Date?) -> String {
        guard let date else { return "" }
        let f = DateFormatter()
        f.dateFormat = "d MMM"
        return f.string(from: date)
    }

    // MARK: - Empty States

    @ViewBuilder
    private var emptyState: some View {
        FrostCard(padding: Theme.s4) {
            VStack(spacing: Theme.s4) {
                Image(systemName: showResults ? "clock" : "calendar")
                    .font(.system(size: 32))
                    .foregroundStyle(Theme.textMute)
                Text(showResults
                    ? "No results yet — first picks score after kickoff."
                    : "All caught up.")
                    .font(.bodyX)
                    .foregroundStyle(Theme.textDim)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, Theme.s8)
        }
    }
}
