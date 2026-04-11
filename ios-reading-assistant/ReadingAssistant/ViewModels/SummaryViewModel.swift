import Foundation

@MainActor
final class SummaryViewModel: ObservableObject {
    @Published var summary: SummaryResponse?
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let aiService: AIServiceProtocol
    private let cache: SummaryCacheProtocol

    init(aiService: AIServiceProtocol, cache: SummaryCacheProtocol) {
        self.aiService = aiService
        self.cache = cache
    }

    func summarize(book: ImportedBook, content: String) async {
        if let cached = cache.fetchSummary(for: book.id) {
            summary = cached
            return
        }

        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let result = try await aiService.summarize(request: .init(bookID: book.id, title: book.title, content: content))
            summary = result
            cache.saveSummary(result, for: book.id)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
