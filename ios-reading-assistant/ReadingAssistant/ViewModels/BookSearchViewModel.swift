import Foundation

@MainActor
final class BookSearchViewModel: ObservableObject {
    @Published var keyword = ""
    @Published var results: [BookSearchResult] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let doubanService: DoubanServiceProtocol

    init(doubanService: DoubanServiceProtocol) {
        self.doubanService = doubanService
    }

    func search() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            results = try await doubanService.searchBooks(keyword: keyword)
        } catch {
            errorMessage = error.localizedDescription
            results = []
        }
    }
}
