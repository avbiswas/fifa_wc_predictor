import SwiftUI
struct TeamBadge: View {
    let code: String
    var size: CGFloat = 42
    var body: some View {
        Text(code).font(.system(size: size * 0.28, weight: .semibold))
            .foregroundStyle(Theme.text)
            .frame(width: size, height: size)
            .background(Circle().fill(.ultraThinMaterial))
            .overlay(Circle().fill(Theme.card)).overlay(Circle().strokeBorder(Theme.hairline, lineWidth: 1))
    }
}
