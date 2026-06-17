import SwiftUI

struct InsightsView: View {
    @EnvironmentObject var store: AppStore

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()
            IridescentGlow(intensity: 0.35).ignoresSafeArea()

            if let feed = store.feed {
                NavigationStack {
                    ScrollView {
                        VStack(alignment: .leading, spacing: Theme.s5) {
                            // A) Engine form section
                            Eyebrow(text: "How the picks are doing · last \(feed.form.matches) games")
                                .generativeAppear(0)

                            LazyVGrid(columns: [
                                GridItem(.flexible(), spacing: Theme.s3),
                                GridItem(.flexible(), spacing: Theme.s3)
                            ], spacing: Theme.s3) {
                                MetricTile(
                                    value: "\(feed.form.points)",
                                    caption: "points won",
                                    accent: true
                                )
                                MetricTile(
                                    value: String(format: "%.1f", feed.form.avgPoints),
                                    caption: "avg per game",
                                    accent: false
                                )
                                MetricTile(
                                    value: "\(feed.form.exact)",
                                    caption: "spot-on scores",
                                    accent: true
                                )
                                MetricTile(
                                    value: "\(feed.form.scored)/\(feed.form.matches)",
                                    caption: "games that scored",
                                    accent: false
                                )
                            }
                            .generativeAppear(1)

                            FrostCard {
                                VStack(alignment: .leading, spacing: Theme.s2) {
                                    Sparkline(values: feed.form.recentPoints)
                                    Text("points per pick, most recent on the right")
                                        .font(.calloutX)
                                        .foregroundStyle(Theme.textDim)
                                }
                            }
                            .generativeAppear(2)

                            Text("Scored in \(feed.form.scored) of \(feed.form.matches) and nailed \(feed.form.exact) exact — steady.")
                                .font(.bodyX)
                                .foregroundStyle(Theme.text)
                                .generativeAppear(3)
                        }
                        .padding(.horizontal, Theme.s4)
                        .padding(.top, Theme.s6)
                        .padding(.bottom, 100)
                    }
                    .scrollIndicators(.hidden)
                    .id(store.generation)
                    .refreshable { await store.refresh() }
                    .navigationTitle("Insights")
                }
            } else {
                VStack(spacing: Theme.s4) {
                    ProgressView()
                    Text("Loading insights…")
                        .font(.bodyX)
                        .foregroundStyle(Theme.textDim)
                }
            }
        }
    }
}

// MARK: - MetricTile

private struct MetricTile: View {
    let value: String
    let caption: String
    let accent: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: Theme.s2) {
            Eyebrow(text: caption)
            Text(value)
                .font(.displayX)
                .monospacedDigit()
                .foregroundStyle(accent ? Theme.posText : Theme.text)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(Theme.s4)
        .background(
            RoundedRectangle(cornerRadius: Theme.rMd, style: .continuous)
                .fill(.ultraThinMaterial)
        )
        .background(
            RoundedRectangle(cornerRadius: Theme.rMd, style: .continuous)
                .fill(Theme.card)
        )
        .overlay(
            RoundedRectangle(cornerRadius: Theme.rMd, style: .continuous)
                .strokeBorder(Theme.hairline, lineWidth: 1)
        )
        .shadow(color: Theme.shadow.opacity(0.10), radius: 24, x: 0, y: 14)
    }
}
