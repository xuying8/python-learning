import Foundation

struct BookSearchResult: Identifiable, Codable, Hashable {
    let id = UUID()
    let title: String
    let author: [String]
    let isbn13: String?
    let isbn10: String?
    let imageURL: URL?

    var primaryISBN: String {
        isbn13 ?? isbn10 ?? "N/A"
    }

    enum CodingKeys: String, CodingKey {
        case title
        case author
        case isbn13 = "isbn13"
        case isbn10 = "isbn10"
        case imageURL = "image"
    }
}

struct DoubanBookResponse: Codable {
    let books: [BookSearchResult]
}
