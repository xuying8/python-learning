import CoreData
import Foundation

final class PersistenceController {
    static let shared = PersistenceController()

    let controller: NSPersistentContainer

    init(inMemory: Bool = false) {
        let model = Self.makeModel()
        controller = NSPersistentContainer(name: "ReadingAssistant", managedObjectModel: model)
        if inMemory {
            controller.persistentStoreDescriptions.first?.url = URL(fileURLWithPath: "/dev/null")
        }

        controller.loadPersistentStores { _, error in
            if let error {
                fatalError("CoreData store failed: \(error)")
            }
        }
        controller.viewContext.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
    }

    private static func makeModel() -> NSManagedObjectModel {
        let model = NSManagedObjectModel()

        let book = NSEntityDescription()
        book.name = "BookEntity"
        book.managedObjectClassName = NSStringFromClass(BookEntity.self)

        let bookID = NSAttributeDescription()
        bookID.name = "id"
        bookID.attributeType = .UUIDAttributeType
        bookID.isOptional = false

        let title = NSAttributeDescription()
        title.name = "title"
        title.attributeType = .stringAttributeType
        title.isOptional = false

        let originalPath = NSAttributeDescription()
        originalPath.name = "originalPath"
        originalPath.attributeType = .stringAttributeType
        originalPath.isOptional = false

        let txtPath = NSAttributeDescription()
        txtPath.name = "txtPath"
        txtPath.attributeType = .stringAttributeType
        txtPath.isOptional = false

        let format = NSAttributeDescription()
        format.name = "format"
        format.attributeType = .stringAttributeType
        format.isOptional = false

        let createdAt = NSAttributeDescription()
        createdAt.name = "createdAt"
        createdAt.attributeType = .dateAttributeType
        createdAt.isOptional = false

        book.properties = [bookID, title, originalPath, txtPath, format, createdAt]

        let summary = NSEntityDescription()
        summary.name = "SummaryEntity"
        summary.managedObjectClassName = NSStringFromClass(SummaryEntity.self)

        let summaryBookID = NSAttributeDescription()
        summaryBookID.name = "bookID"
        summaryBookID.attributeType = .UUIDAttributeType
        summaryBookID.isOptional = false

        let summaryText = NSAttributeDescription()
        summaryText.name = "summary"
        summaryText.attributeType = .stringAttributeType
        summaryText.isOptional = false

        let keyPoints = NSAttributeDescription()
        keyPoints.name = "keyPoints"
        keyPoints.attributeType = .transformableAttributeType
        keyPoints.attributeValueClassName = NSStringFromClass(NSArray.self)
        keyPoints.isOptional = false

        let updatedAt = NSAttributeDescription()
        updatedAt.name = "updatedAt"
        updatedAt.attributeType = .dateAttributeType
        updatedAt.isOptional = false

        summary.properties = [summaryBookID, summaryText, keyPoints, updatedAt]

        model.entities = [book, summary]
        return model
    }
}
