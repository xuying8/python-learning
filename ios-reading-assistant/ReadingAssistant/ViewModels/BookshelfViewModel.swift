import CoreData
import Foundation

@MainActor
final class BookshelfViewModel: ObservableObject {
    enum SortType: String, CaseIterable {
        case recent = "Recent"
        case title = "Title"
    }

    @Published var books: [ImportedBook] = []
    @Published var errorMessage: String?
    @Published var searchText = ""
    @Published var sortType: SortType = .recent

    private let context: NSManagedObjectContext
    private let fileImportService: FileImportServiceProtocol

    init(context: NSManagedObjectContext, fileImportService: FileImportServiceProtocol) {
        self.context = context
        self.fileImportService = fileImportService
        loadBooks()
    }

    var filteredBooks: [ImportedBook] {
        var output = books

        if !searchText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            output = output.filter { $0.title.localizedCaseInsensitiveContains(searchText) }
        }

        switch sortType {
        case .recent:
            output.sort { $0.createdAt > $1.createdAt }
        case .title:
            output.sort { $0.title.localizedCaseInsensitiveCompare($1.title) == .orderedAscending }
        }
        return output
    }

    func importBook(from url: URL) {
        do {
            let imported = try fileImportService.importFile(from: url)
            let entity = BookEntity(context: context)
            entity.id = imported.id
            entity.title = imported.title
            entity.originalPath = imported.originalFileURL.path
            entity.txtPath = imported.txtFileURL.path
            entity.format = imported.format.rawValue
            entity.createdAt = imported.createdAt
            try context.save()
            loadBooks()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func loadBooks() {
        let req = NSFetchRequest<BookEntity>(entityName: "BookEntity")
        req.sortDescriptors = [NSSortDescriptor(key: "createdAt", ascending: false)]

        do {
            let entities = try context.fetch(req)
            books = entities.compactMap { entity in
                guard let id = entity.id,
                      let title = entity.title,
                      let original = entity.originalPath,
                      let txt = entity.txtPath,
                      let formatValue = entity.format,
                      let format = BookFormat(rawValue: formatValue),
                      let createdAt = entity.createdAt else { return nil }

                return ImportedBook(
                    id: id,
                    title: title,
                    originalFileURL: URL(fileURLWithPath: original),
                    txtFileURL: URL(fileURLWithPath: txt),
                    format: format,
                    createdAt: createdAt
                )
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
