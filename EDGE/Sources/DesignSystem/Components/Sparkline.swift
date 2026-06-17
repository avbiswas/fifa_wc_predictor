import SwiftUI
struct Sparkline: View {
    let values: [Int]
    private var maxV: Int { max(values.max() ?? 1, 1) }
    var body: some View {
        GeometryReader { geo in
            HStack(alignment: .bottom, spacing: 3) {
                ForEach(values.indices, id: \.self) { i in
                    RoundedRectangle(cornerRadius: 2)
                        .fill(values[i] == 0 ? Theme.track : Theme.iridLilac)
                        .frame(height: max(2, geo.size.height * CGFloat(values[i]) / CGFloat(maxV)))
                }
            }
        }
        .frame(height: 34)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Points history")
        .accessibilityValue("\(values.count) games")
    }
}
