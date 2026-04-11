import Foundation

protocol DoubanServiceProtocol {
    func searchBooks(keyword: String) async throws -> [BookSearchResult]
}

enum ServiceError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case decodingFailed
    case upstream(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid API URL"
        case .invalidResponse: return "Invalid server response"
        case .decodingFailed: return "Failed to parse response"
        case .upstream(let message): return message
        }
    }
}

final class DoubanService: DoubanServiceProtocol {
    private let session: URLSession

    init(session: URLSession = .shared) {
        self.session = session
    }

    func searchBooks(keyword: String) async throws -> [BookSearchResult] {
        guard !keyword.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return [] }
        var components = URLComponents(string: "https://api.douban.com/v2/book/search")
        components?.queryItems = [
            URLQueryItem(name: "q", value: keyword),
            URLQueryItem(name: "count", value: "20")
        ]

        guard let url = components?.url else { throw ServiceError.invalidURL }
        let (data, response) = try await session.data(from: url)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw ServiceError.invalidResponse
        }

        do {
            let decoded = try JSONDecoder().decode(DoubanBookResponse.self, from: data)
            return decoded.books
        } catch {
            throw ServiceError.decodingFailed
        }
    }
}
