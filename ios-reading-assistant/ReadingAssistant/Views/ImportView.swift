import SwiftUI
import UniformTypeIdentifiers

struct ImportView: View {
    @ObservedObject var viewModel: BookshelfViewModel
    @State private var isImporterPresented = false

    var body: some View {
        VStack(spacing: 18) {
            VStack(alignment: .leading, spacing: 10) {
                Label("Supported: EPUB / TXT", systemImage: "doc.badge.plus")
                Label("Local conversion: EPUB → TXT", systemImage: "arrow.triangle.2.circlepath")
                Label("No scraping / no piracy sources", systemImage: "checkmark.shield")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding()
            .background(Color(.secondarySystemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 12))

            Button {
                isImporterPresented = true
            } label: {
                Label("Import From Files", systemImage: "square.and.arrow.down")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)

            if let error = viewModel.errorMessage {
                Text(error).foregroundStyle(.red)
            }

            Spacer()
        }
        .padding()
        .navigationTitle("Import Books")
        .fileImporter(
            isPresented: $isImporterPresented,
            allowedContentTypes: [.plainText, UTType(filenameExtension: "epub") ?? .data],
            allowsMultipleSelection: false
        ) { result in
            switch result {
            case .success(let urls):
                if let url = urls.first {
                    viewModel.importBook(from: url)
                }
            case .failure(let error):
                viewModel.errorMessage = error.localizedDescription
            }
        }
    }
}
