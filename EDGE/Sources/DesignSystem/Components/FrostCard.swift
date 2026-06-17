import SwiftUI
struct FrostCard<Content: View>: View {
    var padding: CGFloat = Theme.s4
    var radius: CGFloat = Theme.rLg
    @ViewBuilder var content: Content
    var body: some View {
        content.padding(padding).frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: radius, style: .continuous).fill(.ultraThinMaterial))
            .background(RoundedRectangle(cornerRadius: radius, style: .continuous).fill(Theme.card))
            .overlay(RoundedRectangle(cornerRadius: radius, style: .continuous)
                .strokeBorder(Theme.hairline, lineWidth: 1))
            .shadow(color: Theme.shadow.opacity(0.10), radius: 24, x: 0, y: 14)
    }
}
