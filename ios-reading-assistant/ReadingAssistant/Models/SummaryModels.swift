import Foundation

struct SummaryRequest {
    let bookID: UUID
    let title: String
    let content: String
}

struct SummaryResponse: Codable {
    let summary: String
    let keyPoints: [String]
}

struct OpenAIChatRequest: Codable {
    struct Message: Codable {
        let role: String
        let content: String
    }

    let model: String
    let messages: [Message]
    let temperature: Double
}

struct OpenAIChatResponse: Codable {
    struct Choice: Codable {
        struct Message: Codable {
            let content: String
        }

        let message: Message
    }

    let choices: [Choice]
}
