import SwiftUI

struct ComponentGallery: View {
    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()
            IridescentGlow(intensity: 0.5).ignoresSafeArea()
            ScrollView {
                VStack(spacing: Theme.s4) {
                    FrostCard {
                        VStack(alignment: .leading, spacing: Theme.s3) {
                            Eyebrow(text: "Ring · 1:0")
                            HStack { Spacer(); SoftRing(value: 1.0/7.0, color: Theme.warnText) { Text("1:0").font(.displayX) }; Spacer() }
                        }
                    }
                    FrostCard {
                        VStack(alignment: .leading, spacing: Theme.s3) {
                            Eyebrow(text: "Strength · POR / COD")
                            StrengthBar(home: 0.74, draw: 0.20, away: 0.06, homeCode: "POR", awayCode: "COD")
                        }
                    }
                    FrostCard {
                        VStack(alignment: .leading, spacing: Theme.s3) {
                            Eyebrow(text: "Gap · you → Alex")
                            GapRail(mine: 18, leader: 24, leaderName: "Alex")
                        }
                    }
                    FrostCard {
                        VStack(alignment: .leading, spacing: Theme.s3) {
                            Eyebrow(text: "Pills · soft state")
                            HStack(spacing: Theme.s2) {
                                SoftPill(text: "Bank it", bg: Theme.posBG, fg: Theme.posText)
                                SoftPill(text: "Coin-flip", bg: Theme.warnBG, fg: Theme.warnText)
                                SoftPill(text: "Wild card", bg: Theme.negBG, fg: Theme.negText)
                                SoftPill(text: "Contrarian", bg: Theme.actBG, fg: Theme.actText)
                            }
                        }
                    }
                    FrostCard {
                        VStack(alignment: .leading, spacing: Theme.s3) {
                            Eyebrow(text: "InkButton · CTA")
                            InkButton(title: "Why this pick") {}
                        }
                    }
                    FrostCard {
                        VStack(alignment: .leading, spacing: Theme.s3) {
                            Eyebrow(text: "Movement · rank delta")
                            HStack(spacing: Theme.s4) {
                                MovementArrow(move: 3)
                                MovementArrow(move: -2)
                                MovementArrow(move: 0)
                            }
                        }
                    }
                    FrostCard {
                        VStack(alignment: .leading, spacing: Theme.s3) {
                            Eyebrow(text: "TeamBadge · BRA")
                            HStack { Spacer(); TeamBadge(code: "BRA"); Spacer() }
                        }
                    }
                    FrostCard {
                        VStack(alignment: .leading, spacing: Theme.s3) {
                            Eyebrow(text: "GeneratedStatus · agentic motif")
                            GeneratedStatus(updatedAt: .now)
                            GeneratedStatus(updatedAt: .now, generating: true)
                        }
                    }
                    FrostCard {
                        VStack(alignment: .leading, spacing: Theme.s3) {
                            Eyebrow(text: "Sparkline · recent points")
                            Sparkline(values: [2, 0, 4, 2, 0, 3, 2, 0, 4])
                        }
                    }
                }
                .padding(Theme.s4)
            }
        }
        .preferredColorScheme(.light)
    }
}
