import SwiftUI
extension Font {
    static let greeting  = Font.system(size: 30, weight: .light,   design: .default)
    static let heroLight = Font.system(size: 48, weight: .light,   design: .default)
    static let displayX  = Font.system(size: 26, weight: .medium,  design: .default)
    static let titleX    = Font.system(size: 20, weight: .medium)
    static let headlineX = Font.system(size: 16, weight: .medium)
    static let bodyX     = Font.system(size: 15, weight: .regular)
    static let calloutX  = Font.system(size: 13, weight: .regular)
    static let eyebrowX  = Font.system(size: 11, weight: .medium)
}
struct Eyebrow: View {            // sentence-case small label, gentle tracking
    let text: String
    var body: some View { Text(text).font(.eyebrowX).tracking(0.6).foregroundStyle(Theme.textDim) }
}
