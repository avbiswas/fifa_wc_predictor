import SwiftUI
struct InkButton: View {
    let title: String
    var systemImage: String = "arrow.right"
    var action: () -> Void
    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Text(title).font(.headlineX).foregroundStyle(.white)
                Image(systemName: systemImage).font(.system(size: 12, weight: .bold))
                    .foregroundStyle(Theme.ink)
                    .frame(width: 22, height: 22).background(Circle().fill(.white))
            }
            .frame(maxWidth: .infinity).padding(.vertical, 13)
            .background(Capsule().fill(Theme.ink))
        }
        .buttonStyle(PressScale())
    }
}
struct PressScale: ButtonStyle {        // subtle tactile press, reused everywhere
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.scaleEffect(configuration.isPressed ? 0.97 : 1)
            .animation(.spring(response: 0.3, dampingFraction: 0.7), value: configuration.isPressed)
    }
}
