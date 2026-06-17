import SwiftUI

@main
struct EDGEApp: App {
    @StateObject private var store = AppStore()

    var body: some Scene {
        WindowGroup {
            ComponentGallery()
                .environmentObject(store)
                .preferredColorScheme(.light)
                .task { await store.load() }
        }
    }
}
