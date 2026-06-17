import Foundation

struct Feed: Codable {
    let updatedAt: Date
    let season: String
    let me: Me
    let strategy: Strategy
    let form: Form
    let table: [TableRow]
    let matches: [Match]
    let scouting: [ScoutReport]
}
struct Me: Codable {
    let name: String; let rank: Int; let points: Int; let playersCount: Int
    let leaderName: String; let leaderPoints: Int; let deficit: Int; let tiebreaker: String
}
struct Strategy: Codable {
    let mode: String; let headline: String; let subtitle: String; let drawPlan: DrawPlan
    struct DrawPlan: Codable { let planned: Int; let reason: String }
}
struct Form: Codable {
    let matches: Int; let points: Int; let avgPoints: Double
    let exact: Int; let scored: Int; let blanked: Int; let recentPoints: [Int]
}
struct TableRow: Codable, Identifiable {
    var id: String { name }
    let rank: Int; let name: String; let points: Int; let move: Int; let isMe: Bool; let isLeader: Bool
}
struct Match: Codable, Identifiable {
    let id: String; let kickoff: Date; let matchday: Int; let status: String
    let home: Team; let away: Team; let result: ScoreResult?
    let myPick: Pick; let odds: Odds; let favorite: String; let favoriteStrength: String
    let upset: Upset; let fieldExposure: FieldExposure; let alternates: [Alternate]; let news: [String]
    struct Team: Codable { let name: String; let code: String; let rank: Int }
    struct ScoreResult: Codable { let home: Int; let away: Int }
    struct Odds: Codable { let home: Double; let draw: Double; let away: Double }
    struct Upset: Codable { let isUpset: Bool; let text: String }
    struct FieldExposure: Codable { let friendsTotal: Int; let onSamePick: Int; let leaderPick: String? }
    struct Alternate: Codable, Identifiable { var id: String { score }
        let score: String; let expectedPoints: Double; let note: String }
}
struct Pick: Codable {
    let score: String; let tier: String; let tierLabel: String
    let leverage: String; let vsLeader: String; let exactChanceOneIn: Int
    let expectedPoints: Double; let reasons: [String]; let result: PickResult?
    struct PickResult: Codable { let points: Int; let outcome: String }
}
struct ScoutReport: Codable, Identifiable {
    var id: String { name }
    let name: String; let rank: Int; let points: Int; let isLeader: Bool
    let tag: String; let blurb: String; let traits: [Trait]
    struct Trait: Codable, Identifiable { var id: String { label }
        let label: String; let value: String; let level: Int }
}
