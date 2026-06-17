import SwiftUI

@MainActor
final class AppStore: ObservableObject {
    enum Phase { case loading, loaded(Feed), failed(String) }
    @Published var phase: Phase = .loading
    @Published var generation: Int = 0

    var feedURL: URL? = nil

    private static let decoder: JSONDecoder = {
        let d = JSONDecoder(); d.dateDecodingStrategy = .iso8601; return d
    }()

    func load() async {
        if let bundled = try? Self.loadBundled() { phase = .loaded(bundled) }
        generation += 1
        guard let url = feedURL else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            phase = .loaded(try Self.decoder.decode(Feed.self, from: data)); generation += 1
        } catch {
            if case .loaded = phase { return }
            phase = .failed(error.localizedDescription)
        }
    }
    func refresh() async { await load() }

    static func loadBundled() throws -> Feed {
        guard let url = Bundle.main.url(forResource: "SampleFeed", withExtension: "json")
        else { throw NSError(domain: "EDGE", code: 1) }
        return try decoder.decode(Feed.self, from: Data(contentsOf: url))
    }
}
