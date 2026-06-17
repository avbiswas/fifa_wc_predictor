import SwiftUI

@main
struct EDGEApp: App {
    var body: some Scene {
        WindowGroup {
            ZStack {
                Theme.bg.ignoresSafeArea()
                Text("EDGE")
                    .font(.heroLight)
                    .foregroundStyle(Theme.text)
            }
            .preferredColorScheme(.light)
        }
    }
}
