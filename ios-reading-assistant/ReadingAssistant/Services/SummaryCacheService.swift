import CoreData
import Foundation

protocol SummaryCacheProtocol {
    func fetchSummary(for bookID: UUID) -> SummaryResponse?
    func saveSummary(_ summary: SummaryResponse, for bookID: UUID)
}

final class SummaryCacheService: SummaryCacheProtocol {
    private let context: NSManagedObjectContext

    init(context: NSManagedObjectContext) {
        self.context = context
    }

    func fetchSummary(for bookID: UUID) -> SummaryResponse? {
        let req = NSFetchRequest<SummaryEntity>(entityName: "SummaryEntity")
        req.fetchLimit = 1
        req.predicate = NSPredicate(format: "bookID == %@", bookID as CVarArg)
        guard let entity = try? context.fetch(req).first,
              let summary = entity.summary,
              let keyPoints = entity.keyPoints as? [String] else { return nil }
        return SummaryResponse(summary: summary, keyPoints: keyPoints)
    }

    func saveSummary(_ summary: SummaryResponse, for bookID: UUID) {
        let req = NSFetchRequest<SummaryEntity>(entityName: "SummaryEntity")
        req.fetchLimit = 1
        req.predicate = NSPredicate(format: "bookID == %@", bookID as CVarArg)
        let entity = (try? context.fetch(req).first) ?? SummaryEntity(context: context)
        entity.bookID = bookID
        entity.summary = summary.summary
        entity.keyPoints = summary.keyPoints as NSObject
        entity.updatedAt = Date()
        try? context.save()
    }
}
