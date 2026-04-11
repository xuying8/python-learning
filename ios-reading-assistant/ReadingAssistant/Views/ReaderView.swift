import SwiftUI

struct ReaderView: View {
    let book: ImportedBook
    @ObservedObject var readerViewModel: ReaderViewModel
    @ObservedObject var summaryViewModel: SummaryViewModel

    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Stepper("Font \(Int(readerViewModel.fontSize))", value: $readerViewModel.fontSize, in: 12...30)
                Spacer()
                Button("Summarize") {
                    Task {
                        await summaryViewModel.summarize(book: book, content: readerViewModel.content)
                    }
                }
                .buttonStyle(.bordered)
            }

            ScrollView {
                Text(readerViewModel.pages[safe: readerViewModel.currentPage] ?? "")
                    .font(.system(size: readerViewModel.fontSize))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.vertical)
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
        }
    }
}

private struct SummaryCard: View {
    let summary: SummaryResponse

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Summary").font(.headline)
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
