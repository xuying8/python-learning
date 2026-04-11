import CoreData
import Foundation

@objc(BookEntity)
final class BookEntity: NSManagedObject {
    @NSManaged var id: UUID?
    @NSManaged var title: String?
    @NSManaged var originalPath: String?
    @NSManaged var txtPath: String?
    @NSManaged var format: String?
    @NSManaged var createdAt: Date?
}

@objc(SummaryEntity)
final class SummaryEntity: NSManagedObject {
    @NSManaged var bookID: UUID?
    @NSManaged var summary: String?
    @NSManaged var keyPoints: NSObject?
    @NSManaged var updatedAt: Date?
}
