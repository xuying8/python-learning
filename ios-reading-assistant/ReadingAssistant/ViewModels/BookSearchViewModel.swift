import Foundation

@MainActor
final class BookSearchViewModel: ObservableObject {
    @Published var keyword = ""
    @Published var results: [BookSearchResult] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var recentKeywords: [String] = []

    private let doubanService: DoubanServiceProtocol

    init(doubanService: DoubanServiceProtocol) {
        self.doubanService = doubanService
    }

    func search() async {
        let trimmed = keyword.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            results = []
            return
        }

        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            results = try await doubanService.searchBooks(keyword: trimmed)
            appendRecent(trimmed)
        } catch {
            errorMessage = error.localizedDescription
            results = []
        }
    }

    func applyRecent(_ text: String) {
        keyword = text
    }

    private func appendRecent(_ text: String) {
        recentKeywords.removeAll { $0.caseInsensitiveCompare(text) == .orderedSame }
        recentKeywords.insert(text, at: 0)
        recentKeywords = Array(recentKeywords.prefix(8))
    }
}
