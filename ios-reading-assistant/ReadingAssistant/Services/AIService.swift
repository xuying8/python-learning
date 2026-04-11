import Foundation

protocol AIServiceProtocol {
    func summarize(request: SummaryRequest) async throws -> SummaryResponse
}

final class AIService: AIServiceProtocol {
    private let session: URLSession
    private let endpoint: URL
    private let apiKey: String
    private let model: String

    init(
        session: URLSession = .shared,
        endpoint: URL = URL(string: "https://api.openai.com/v1/chat/completions")!,
        apiKey: String = ProcessInfo.processInfo.environment["OPENAI_API_KEY"] ?? "",
        model: String = "gpt-4o-mini"
    ) {
        self.session = session
        self.endpoint = endpoint
        self.apiKey = apiKey
        self.model = model
    }

    func summarize(request: SummaryRequest) async throws -> SummaryResponse {
        guard !apiKey.isEmpty else {
            throw ServiceError.upstream("Missing API key. Configure OPENAI_API_KEY.")
        }

        let chunks = request.content.chunked(maxCharacters: 4_000)
        var partialSummaries: [String] = []
        for chunk in chunks {
            let partial = try await summarizeChunk(chunk, title: request.title)
            partialSummaries.append(partial)
        }

        let mergedText = partialSummaries.joined(separator: "\n")
        let finalPrompt = """
        Based on the partial summaries below, return strict JSON:
        {"summary":"...","keyPoints":["...","..."]}

        Partial summaries:
        \(mergedText)
        """

        let response = try await callChat(prompt: finalPrompt)
        guard let data = response.data(using: .utf8),
              let summary = try? JSONDecoder().decode(SummaryResponse.self, from: data) else {
            throw ServiceError.decodingFailed
        }
        return summary
    }

    private func summarizeChunk(_ text: String, title: String) async throws -> String {
        let prompt = """
        Summarize this book chunk from '\(title)' in <= 120 words.

        \(text)
        """
        return try await callChat(prompt: prompt)
    }

    private func callChat(prompt: String) async throws -> String {
        var urlRequest = URLRequest(url: endpoint)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")

        let body = OpenAIChatRequest(
            model: model,
            messages: [
                .init(role: "system", content: "You are a reading assistant. Return concise output."),
                .init(role: "user", content: prompt)
            ],
            temperature: 0.2
        )
        urlRequest.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: urlRequest)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw ServiceError.invalidResponse
        }

        let decoded = try JSONDecoder().decode(OpenAIChatResponse.self, from: data)
        guard let content = decoded.choices.first?.message.content else {
            throw ServiceError.decodingFailed
        }
        return content.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}

private extension String {
    func chunked(maxCharacters: Int) -> [String] {
        guard count > maxCharacters else { return [self] }
        var chunks: [String] = []
        var start = startIndex
        while start < endIndex {
            let end = index(start, offsetBy: maxCharacters, limitedBy: endIndex) ?? endIndex
            chunks.append(String(self[start..<end]))
            start = end
        }
        return chunks
    }
}
