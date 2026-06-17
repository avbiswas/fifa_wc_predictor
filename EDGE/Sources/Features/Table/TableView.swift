import SwiftUI

struct TableView: View {
    @EnvironmentObject var store: AppStore
    @State private var scouted: ScoutReport?

    var body: some View {
        Group {
            if let feed = store.feed {
                ScrollView {
                    VStack(alignment: .leading, spacing: Theme.s4) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("League")
                                .font(.titleX)
                                .foregroundStyle(Theme.ink)
                            Text("\(feed.me.playersCount) players · \(feed.me.tiebreaker) decides ties")
                                .font(.calloutX)
                                .foregroundStyle(Theme.textDim)
                        }
                        .generativeAppear(0)

                        GapRail(mine: feed.me.points,
                                leader: feed.me.leaderPoints,
                                leaderName: feed.me.leaderName)
                            .generativeAppear(1)

                        FrostCard {
                            VStack(spacing: 0) {
                                ForEach(Array(feed.table.enumerated()), id: \.element.id) { offset, row in
                                    if offset > 0 { Divider().background(Theme.hairline) }
                                    tableRow(row, scouting: feed.scouting)
                                        .generativeAppear(offset)
                                }
                            }
                        }
                    }
                    .padding(.horizontal, Theme.s4)
                    .padding(.top, Theme.s6)
                    .id(store.generation)
                }
                .refreshable { await store.refresh() }
            } else {
                FrostCard {
                    Text("Loading the league…")
                        .font(.titleX)
                        .foregroundStyle(Theme.textDim)
                }
                .padding(.horizontal, Theme.s4)
                .padding(.top, Theme.s6)
            }
        }
        .navigationTitle("Table")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(item: $scouted) { report in
            ScoutCard(report: report)
                .padding()
                .presentationDetents([.medium])
                .presentationBackground(Theme.bg)
        }
    }

    @ViewBuilder
    private func tableRow(_ row: TableRow, scouting: [ScoutReport]) -> some View {
        HStack(spacing: Theme.s3) {
            Text("#\(row.rank)")
                .font(.headlineX)
                .monospacedDigit()
                .foregroundStyle(row.rank == 1 ? Theme.actText : Theme.textDim)
                .frame(width: 30, alignment: .leading)

            if row.isLeader {
                Image(systemName: "crown.fill")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(Theme.actText)
            }

            Text(row.name)
                .font(.headlineX)
                .foregroundStyle(row.isMe ? Theme.ink : Theme.text)

            if row.isMe {
                SoftPill(text: "you")
            }

            Spacer()

            Text("\(row.points)")
                .font(.headlineX)
                .monospacedDigit()
                .foregroundStyle(Theme.ink)

            MovementArrow(move: row.move)
        }
        .padding(.vertical, Theme.s3)
        .padding(.horizontal, Theme.s2)
        .background {
            if row.isMe {
                RoundedRectangle(cornerRadius: Theme.rSm, style: .continuous)
                    .fill(Theme.actBG.opacity(0.5))
            }
        }
        .overlay(alignment: .leading) {
            if row.isMe {
                RoundedRectangle(cornerRadius: 2, style: .continuous)
                    .fill(LinearGradient(colors: [Theme.iridBlue, Theme.iridLilac, Theme.iridBlush],
                                         startPoint: .top, endPoint: .bottom))
                    .frame(width: 3)
                    .padding(.vertical, 2)
            }
        }
        .contentShape(Rectangle())
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("#\(row.rank) \(row.name), \(row.points) points\(row.isMe ? ", you" : "")\(row.isLeader ? ", leader" : "").")
        .accessibilityHint(row.isMe ? "" : "Double-tap for scouting report")
        .onTapGesture {
            if !row.isMe, let match = scouting.first(where: { $0.name == row.name }) {
                scouted = match
            }
        }
    }
}
