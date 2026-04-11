import SwiftUI
import UniformTypeIdentifiers

struct ImportView: View {
    @ObservedObject var viewModel: BookshelfViewModel
    @State private var isImporterPresented = false

    var body: some View {
        VStack(spacing: 16) {
            Text("Import EPUB/TXT files from Files app.")
                .font(.subheadline)

            Button("Select File") {
                isImporterPresented = true
            }
            .buttonStyle(.borderedProminent)

            if let error = viewModel.errorMessage {
                Text(error).foregroundStyle(.red)
            }
        }
        .padding()
        .navigationTitle("Import")
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
