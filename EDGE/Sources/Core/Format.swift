import SwiftUI
enum Format {

    // Tier → soft pill style (label + fg + bg) and a ring color
    static func tierStyle(_ tier: String, label: String) -> (text: String, fg: Color, bg: Color) {
        switch tier {
        case "strong":    return (label.isEmpty ? "Bank it"   : label, Theme.posText,  Theme.posBG)
        case "normal":    return (label.isEmpty ? "Solid pick": label, Theme.posText,  Theme.posBG)
        case "thin_edge": return (label.isEmpty ? "Coin-flip" : label, Theme.warnText, Theme.warnBG)
        default:          return (label.isEmpty ? "Wild card" : label, Theme.negText,  Theme.negBG)
        }
    }
    static func tierRingColor(_ tier: String) -> Color {
        switch tier { case "strong","normal": return Theme.posText
                      case "thin_edge": return Theme.warnText
                      default: return Theme.negText }
    }

    static func strengthWords(_ key: String) -> String {
        switch key { case "heavy": return "Heavy favorite"; case "clear": return "Clear favorite"
                     case "slight": return "Slight edge"; default: return "Even game" }
    }
    static func leverageChip(_ l: String) -> (text: String, fg: Color, bg: Color, icon: String) {
        l == "contrarian" ? ("Against the room", Theme.actText, Theme.actBG, "arrow.triangle.branch")
                          : ("With the room",    Theme.textDim, Color(hex: "F0F0F3"), "person.3")
    }
    static func leaderChip(_ v: String, leaderName: String) -> (text: String, fg: Color, bg: Color) {
        v == "different" ? ("Different from \(leaderName)", Theme.actText, Theme.actBG)
                         : ("Same as \(leaderName)",        Theme.textDim, Color(hex: "F0F0F3"))
    }
    static func ringFill(oneIn: Int) -> Double { oneIn <= 0 ? 0 : 1.0 / Double(oneIn) }
    static func chanceText(oneIn: Int) -> String { "1 in \(max(oneIn,1))" }

    static func outcomeChip(_ outcome: String, points: Int) -> (text: String, fg: Color, bg: Color) {
        switch outcome {
        case "exact":    return ("Spot on  +\(points)",        Theme.posText, Theme.posBG)
        case "goaldiff": return ("Right margin  +\(points)",   Theme.posText, Theme.posBG)
        case "tendency": return ("Right winner  +\(points)",   Theme.posText, Theme.posBG)
        case "draw":     return ("Called the draw  +\(points)",Theme.posText, Theme.posBG)
        default:         return ("Missed  +0",                 Theme.negText, Theme.negBG)
        }
    }
    static func modeIcon(_ mode: String) -> String {
        switch mode { case "safe": return "shield"; case "balanced": return "scalemass"
            case "controlled_attack": return "scope"; case "desperation": return "flame"
            case "protect_spieltag_win": return "lock"; default: return "scope" }
    }
    static func greeting(_ name: String, date: Date = Date()) -> String {
        let h = Calendar.current.component(.hour, from: date)
        let part = h < 12 ? "Good morning" : (h < 18 ? "Good afternoon" : "Good evening")
        return "\(part), \(name)."
    }
    static func countdown(to date: Date) -> String {
        let s = Int(date.timeIntervalSinceNow); if s <= 0 { return "Kicking off" }
        let h = s/3600, m = (s%3600)/60
        if h >= 24 { return "in \(h/24)d \(h%24)h" }
        return h >= 1 ? "in \(h)h \(m)m" : "in \(m)m"
    }
    static func kickoffClock(_ d: Date) -> String { let f = DateFormatter(); f.dateFormat = "HH:mm"; return f.string(from: d) }
    static func relativeUpdated(_ d: Date) -> String {
        let r = RelativeDateTimeFormatter(); r.unitsStyle = .short; return r.localizedString(for: d, relativeTo: Date())
    }
}
