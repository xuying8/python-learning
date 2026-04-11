import Foundation
import SwiftSoup
import ZIPFoundation

enum EPUBConverter {
    static func convertEPUBToText(epubURL: URL) throws -> String {
        let tempDir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: tempDir, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: tempDir) }

        guard let archive = Archive(url: epubURL, accessMode: .read) else {
            throw ServiceError.upstream("Unable to open EPUB archive.")
        }

        for entry in archive {
            let destination = tempDir.appendingPathComponent(entry.path)
            let parent = destination.deletingLastPathComponent()
            try FileManager.default.createDirectory(at: parent, withIntermediateDirectories: true)
            _ = try archive.extract(entry, to: destination)
        }

        let enumerator = FileManager.default.enumerator(at: tempDir, includingPropertiesForKeys: nil)
        let htmlFiles = (enumerator?.allObjects as? [URL] ?? [])
            .filter { ["html", "xhtml", "htm"].contains($0.pathExtension.lowercased()) }
            .sorted { $0.path < $1.path }

        var merged: [String] = []
        for htmlURL in htmlFiles {
            let raw = try String(contentsOf: htmlURL, encoding: .utf8)
            let doc = try SwiftSoup.parse(raw)
            let text = try doc.text()
            if !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                merged.append(text)
            }
        }

        guard !merged.isEmpty else {
            throw ServiceError.upstream("No readable content found in EPUB.")
        }

        return merged.joined(separator: "\n\n")
    }
}
