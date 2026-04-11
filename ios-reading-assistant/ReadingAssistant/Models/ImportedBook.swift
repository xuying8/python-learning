import Foundation

enum BookFormat: String, Codable {
    case txt
    case epub
}

struct ImportedBook: Identifiable, Hashable {
    let id: UUID
    let title: String
    let originalFileURL: URL
    let txtFileURL: URL
    let format: BookFormat
    let createdAt: Date
}
