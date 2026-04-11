import SwiftUI

struct BookSearchView: View {
    @ObservedObject var viewModel: BookSearchViewModel

    var body: some View {
        VStack(spacing: 12) {
            HStack {
                TextField("Search title / ISBN", text: $viewModel.keyword)
                    .textFieldStyle(.roundedBorder)
                Button("Go") {
                    Task { await viewModel.search() }
                }
                .buttonStyle(.borderedProminent)
            }

            if viewModel.isLoading {
                ProgressView("Searching...")
            }

            if let error = viewModel.errorMessage {
                Text(error)
                    .foregroundStyle(.red)
            }

            List(viewModel.results) { book in
                VStack(alignment: .leading, spacing: 6) {
                    Text(book.title).font(.headline)
                    Text(book.author.joined(separator: ", ")).font(.subheadline)
                    Text("ISBN: \(book.primaryISBN)").font(.caption)
                }
            }
            .listStyle(.plain)
        }
        .padding()
        .navigationTitle("Douban Search")
    }
}
