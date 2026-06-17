import SwiftUI

extension AppStore {
    var feed: Feed? {
        if case .loaded(let f) = phase { return f }
        return nil
    }
}

enum Tab: String, CaseIterable {
    case today, matches, table, insights

    var title: String {
        switch self {
        case .today: return "Today"
        case .matches: return "Matches"
        case .table: return "Table"
        case .insights: return "Insights"
        }
    }

    var icon: String {
        switch self {
        case .today: return "sparkles"
        case .matches: return "soccerball"
        case .table: return "trophy"
        case .insights: return "chart.bar"
        }
    }
}

struct RootView: View {
    @EnvironmentObject var store: AppStore
    @State private var tab: Tab = .today

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()
            IridescentGlow(intensity: tab == .today ? 1.0 : 0.35).ignoresSafeArea()
            TabView(selection: $tab) {
                ForEach(Tab.allCases, id: \.self) { t in
                    NavigationStack { PlaceholderTab(tab: t) }
                        .tag(t)
                }
            }
            .toolbar(.hidden, for: .tabBar)
        }
    }
}

private struct PlaceholderTab: View {
    let tab: Tab
    var body: some View {
        ScrollView {
            FrostCard {
                Text("\(tab.title) — coming soon")
                    .font(.titleX)
                    .foregroundStyle(Theme.text)
            }
            .padding(.horizontal, Theme.s4)
            .padding(.top, Theme.s6)
        }
    }
}
