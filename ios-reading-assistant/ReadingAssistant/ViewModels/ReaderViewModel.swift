import Foundation

@MainActor
final class ReaderViewModel: ObservableObject {
    @Published var content = ""
    @Published var currentPage = 0
    @Published var fontSize: Double = 17
    @Published var errorMessage: String?

    private let fileImportService: FileImportServiceProtocol

    init(fileImportService: FileImportServiceProtocol) {
        self.fileImportService = fileImportService
    }

    var pages: [String] {
        content.chunked(maxCharacters: 1_800)
    }

    func load(book: ImportedBook) {
        do {
            content = try fileImportService.readText(from: book.txtFileURL)
            currentPage = 0
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func nextPage() {
        guard currentPage + 1 < pages.count else { return }
        currentPage += 1
    }

    func previousPage() {
        guard currentPage > 0 else { return }
        currentPage -= 1
    }
}

private extension String {
    func chunked(maxCharacters: Int) -> [String] {
        guard !isEmpty else { return [""] }
        var result: [String] = []
        var start = startIndex
        while start < endIndex {
            let end = index(start, offsetBy: maxCharacters, limitedBy: endIndex) ?? endIndex
            result.append(String(self[start..<end]))
            start = end
        }
        return result
    }
}
