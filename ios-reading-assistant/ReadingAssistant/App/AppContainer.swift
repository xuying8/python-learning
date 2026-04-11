import Foundation

final class AppContainer: ObservableObject {
    let persistence = PersistenceController.shared

    lazy var doubanService: DoubanServiceProtocol = DoubanService()
    lazy var fileImportService: FileImportServiceProtocol = FileImportService()
    lazy var aiService: AIServiceProtocol = AIService()
    lazy var summaryCache: SummaryCacheProtocol = SummaryCacheService(context: persistence.controller.viewContext)

    lazy var readerViewModel: ReaderViewModel = {
        ReaderViewModel(fileImportService: fileImportService)
    }()

    lazy var bookshelfViewModel: BookshelfViewModel = {
        BookshelfViewModel(context: persistence.controller.viewContext, fileImportService: fileImportService)
    }()

    lazy var searchViewModel: BookSearchViewModel = {
        BookSearchViewModel(doubanService: doubanService)
    }()

    lazy var summaryViewModel: SummaryViewModel = {
        SummaryViewModel(aiService: aiService, cache: summaryCache)
    }()
}
