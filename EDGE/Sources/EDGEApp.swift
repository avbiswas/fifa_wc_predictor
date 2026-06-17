import SwiftUI

@main
struct EDGEApp: App {
    @StateObject private var store = AppStore()

    var body: some Scene {
        WindowGroup {
            ZStack {
                Theme.bg.ignoresSafeArea()
                IridescentGlow().ignoresSafeArea()
                VStack(spacing: 8) {
                    Text("EDGE").font(.heroLight)
                    Text("agentic gen UI").font(.calloutX).foregroundStyle(Theme.textDim)
                }
                .generativeAppear(0)
            }
            .environmentObject(store)
            .preferredColorScheme(.light)
            .task { await store.load() }
        }
    }
}
