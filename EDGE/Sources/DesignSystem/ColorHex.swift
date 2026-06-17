import SwiftUI
extension Color {
    init(hex: String) {
        let s = Scanner(string: hex.trimmingCharacters(in: .alphanumerics.inverted))
        var v: UInt64 = 0; s.scanHexInt64(&v)
        self = Color(red: Double((v & 0xFF0000) >> 16)/255,
                     green: Double((v & 0x00FF00) >> 8)/255,
                     blue: Double(v & 0x0000FF)/255)
    }
}
