import SwiftUI

struct ReaderView: View {
    let book: ImportedBook
    @ObservedObject var readerViewModel: ReaderViewModel
    @ObservedObject var summaryViewModel: SummaryViewModel
    @State private var sliderProgress: Double = 0

    var body: some View {
        VStack(spacing: 12) {
            controls

            ScrollView {
                Text(readerViewModel.pages[safe: readerViewModel.currentPage] ?? "")
                    .font(.system(size: readerViewModel.fontSize))
                    .foregroundStyle(themeForeground)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()
            }
            .background(themeBackground)
            .clipShape(RoundedRectangle(cornerRadius: 14))

            Slider(value: $sliderProgress, in: 0...1) { _ in
                readerViewModel.jumpTo(progress: sliderProgress)
            }
            .onAppear { sliderProgress = readerViewModel.progress }
            .onChange(of: readerViewModel.currentPage) { _ in
                sliderProgress = readerViewModel.progress
            }

            HStack {
                Button("Prev") { readerViewModel.previousPage() }
                Spacer()
                Text("\(readerViewModel.currentPage + 1)/\(max(readerViewModel.pages.count, 1))")
                    .font(.caption)
                Spacer()
                Button("Next") { readerViewModel.nextPage() }
            }

            if summaryViewModel.isLoading {
                ProgressView("Summarizing...")
            }

            if let summary = summaryViewModel.summary {
                SummaryCard(summary: summary)
            }
        }
        .padding()
        .navigationTitle(book.title)
        .navigationBarTitleDisplayMode(.inline)
        .task {
            readerViewModel.load(book: book)
            sliderProgress = readerViewModel.progress
        }
    }

    private var controls: some View {
        HStack {
            Stepper("Font \(Int(readerViewModel.fontSize))", value: $readerViewModel.fontSize, in: 12...30)
            Spacer()
            Menu {
                ForEach(ReaderViewModel.ReaderTheme.allCases, id: \.self) { theme in
                    Button(theme.rawValue) { readerViewModel.theme = theme }
                }
            } label: {
                Label(readerViewModel.theme.rawValue, systemImage: "paintpalette")
            }
            Button("Summarize") {
                Task {
                    await summaryViewModel.summarize(book: book, content: readerViewModel.content)
                }
            }
            .buttonStyle(.borderedProminent)
        }
    }

    private var themeBackground: Color {
        switch readerViewModel.theme {
        case .system: return Color(.systemBackground)
        case .sepia: return Color(red: 0.96, green: 0.92, blue: 0.84)
        case .dark: return Color.black
        }
    }

    private var themeForeground: Color {
        readerViewModel.theme == .dark ? .white : .primary
    }
}

private struct SummaryCard: View {
    let summary: SummaryResponse

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("AI Summary").font(.headline)
                Spacer()
                ShareLink(item: summary.summary) {
                    Image(systemName: "square.and.arrow.up")
                }
            }
            Text(summary.summary).font(.subheadline)
            Text("Key Points").font(.headline)
            ForEach(summary.keyPoints, id: \.self) { point in
                Text("• \(point)")
            }
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}

private extension Array {
    subscript(safe index: Int) -> Element? {
        guard indices.contains(index) else { return nil }
        return self[index]
    }
}
