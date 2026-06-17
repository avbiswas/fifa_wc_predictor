import SwiftUI
enum Theme {
    // Surfaces
    static let bg       = Color(hex: "FCFCFE")          // app canvas (near white)
    static let card     = Color.white.opacity(0.55)     // frosted fill (over material)
    static let hairline = Color.white.opacity(0.85)     // 1px top-highlight border
    static let track    = Color(hex: "ECECF1")          // empty rail/ring track
    static let shadow   = Color(hex: "282A46")          // soft bluish shadow color (use ~0.10)

    // Text
    static let text     = Color(hex: "2B2B2E")
    static let textDim  = Color(hex: "9A9AA1")
    static let textMute = Color(hex: "BFC0C6")
    static let ink      = Color(hex: "161618")          // black CTA + strong text

    // Iridescent palette (the hero gradient)
    static let iridBlue  = Color(hex: "B9C9F2")
    static let iridLilac = Color(hex: "E7CDEE")
    static let iridBlush = Color(hex: "F6D4DC")
    static let iridPeach = Color(hex: "F8E7C8")
    static let iridMint  = Color(hex: "CBEBD9")
    static let spark     = Color(hex: "9B8CF0")         // the "generating" accent dot

    // Soft state pairs (pastel fill + darker same-hue text). Never neon.
    static let posBG = Color(hex: "DDF3E7"); static let posText = Color(hex: "1F7A52")  // good / win / up
    static let warnBG = Color(hex: "FBEBD3"); static let warnText = Color(hex: "9A6512") // coin-flip
    static let negBG = Color(hex: "FBE3E0"); static let negText = Color(hex: "B5483A")   // loss / risk / down
    static let actBG = Color(hex: "E7E6FB"); static let actText = Color(hex: "5B4FC0")   // active / contrarian

    // Spacing
    static let s1: CGFloat = 4;  static let s2: CGFloat = 8;  static let s3: CGFloat = 12
    static let s4: CGFloat = 16; static let s5: CGFloat = 20; static let s6: CGFloat = 24
    static let s8: CGFloat = 32; static let s10: CGFloat = 40
    // Radii
    static let rSm: CGFloat = 14; static let rMd: CGFloat = 20; static let rLg: CGFloat = 26; static let rXl: CGFloat = 34
}
