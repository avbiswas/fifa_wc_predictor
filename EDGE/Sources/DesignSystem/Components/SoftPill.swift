import SwiftUI
struct SoftPill: View {
    let text: String
    var bg: Color = Theme.actBG
    var fg: Color = Theme.actText
    var systemImage: String? = nil
    var body: some View {
        HStack(spacing: 5) {
            if let s = systemImage { Image(systemName: s).font(.system(size: 10, weight: .semibold)) }
            Text(text).font(.eyebrowX)
        }
        .foregroundStyle(fg)
        .padding(.horizontal, 9).padding(.vertical, 5)
        .background(Capsule().fill(bg))
    }
}
