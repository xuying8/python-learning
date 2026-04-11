import Foundation
import UniformTypeIdentifiers

protocol FileImportServiceProtocol {
    func importFile(from securityScopedURL: URL) throws -> ImportedBook
    func readText(from url: URL) throws -> String
    func documentsDirectory() -> URL
}

enum FileImportError: Error, LocalizedError {
    case unsupportedType
    case accessDenied

    var errorDescription: String? {
        switch self {
        case .unsupportedType: return "Only EPUB and TXT files are supported."
        case .accessDenied: return "Unable to access imported file."
        }
    }
}

final class FileImportService: FileImportServiceProtocol {
    func importFile(from securityScopedURL: URL) throws -> ImportedBook {
        guard securityScopedURL.startAccessingSecurityScopedResource() else {
            throw FileImportError.accessDenied
        }
        defer { securityScopedURL.stopAccessingSecurityScopedResource() }

        let ext = securityScopedURL.pathExtension.lowercased()
        let format: BookFormat
        switch ext {
        case "txt": format = .txt
        case "epub": format = .epub
        default: throw FileImportError.unsupportedType
        }

        let destinationFolder = documentsDirectory().appendingPathComponent("Books", isDirectory: true)
        try FileManager.default.createDirectory(at: destinationFolder, withIntermediateDirectories: true)

        let id = UUID()
        let originalDestination = destinationFolder.appendingPathComponent("\(id.uuidString).\(ext)")
        if FileManager.default.fileExists(atPath: originalDestination.path) {
            try FileManager.default.removeItem(at: originalDestination)
        }
        try FileManager.default.copyItem(at: securityScopedURL, to: originalDestination)

        let txtURL: URL
        if format == .epub {
            txtURL = destinationFolder.appendingPathComponent("\(id.uuidString).txt")
            let converted = try EPUBConverter.convertEPUBToText(epubURL: originalDestination)
            try converted.write(to: txtURL, atomically: true, encoding: .utf8)
        } else {
            txtURL = originalDestination
        }

        return ImportedBook(
            id: id,
            title: securityScopedURL.deletingPathExtension().lastPathComponent,
            originalFileURL: originalDestination,
            txtFileURL: txtURL,
            format: format,
            createdAt: Date()
        )
    }

    func readText(from url: URL) throws -> String {
        try String(contentsOf: url, encoding: .utf8)
    }

    func documentsDirectory() -> URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }
}
