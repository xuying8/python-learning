import Foundation

@MainActor
final class ReaderViewModel: ObservableObject {
    enum ReaderTheme: String, CaseIterable {
        case system = "System"
        case sepia = "Sepia"
        case dark = "Dark"
    }

    @Published var content = ""
    @Published var currentPage = 0
    @Published var fontSize: Double = 17
    @Published var errorMessage: String?
    @Published var theme: ReaderTheme = .system

    private let fileImportService: FileImportServiceProtocol

    init(fileImportService: FileImportServiceProtocol) {
        self.fileImportService = fileImportService
    }

    var pages: [String] {
        content.chunked(maxCharacters: 1_800)
    }

    var progress: Double {
        guard !pages.isEmpty else { return 0 }
        return Double(currentPage + 1) / Double(max(pages.count, 1))
    }

    func jumpTo(progress: Double) {
        guard !pages.isEmpty else { return }
        let clamped = min(max(progress, 0), 1)
        let target = Int((Double(pages.count - 1) * clamped).rounded())
        currentPage = target
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
