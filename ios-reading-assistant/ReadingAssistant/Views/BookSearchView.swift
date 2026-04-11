import SwiftUI

struct BookSearchView: View {
    @ObservedObject var viewModel: BookSearchViewModel

    var body: some View {
        VStack(spacing: 14) {
            HStack(spacing: 10) {
                Image(systemName: "book.pages")
                    .foregroundStyle(.secondary)
                TextField("Search by title / ISBN", text: $viewModel.keyword)
                    .textInputAutocapitalization(.never)
                Button("Search") {
                    Task { await viewModel.search() }
                }
                .buttonStyle(.borderedProminent)
            }
            .padding(12)
            .background(Color(.secondarySystemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 12))

            if !viewModel.recentKeywords.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack {
                        ForEach(viewModel.recentKeywords, id: \.self) { keyword in
                            Button(keyword) {
                                viewModel.applyRecent(keyword)
                                Task { await viewModel.search() }
                            }
                            .buttonStyle(.bordered)
                        }
                    }
                }
            }

            if viewModel.isLoading {
                ProgressView("Searching Douban...")
            }

            if let error = viewModel.errorMessage {
                Label(error, systemImage: "exclamationmark.triangle")
                    .foregroundStyle(.red)
            }

            List(viewModel.results) { book in
                HStack(alignment: .top, spacing: 12) {
                    AsyncImage(url: book.imageURL) { image in
                        image.resizable().scaledToFill()
                    } placeholder: {
                        ZStack {
                            Color.gray.opacity(0.15)
                            Image(systemName: "book")
                                .foregroundStyle(.secondary)
                        }
                    }
                    .frame(width: 54, height: 74)
                    .clipShape(RoundedRectangle(cornerRadius: 8))

                    VStack(alignment: .leading, spacing: 6) {
                        Text(book.title).font(.headline)
                        Text(book.author.joined(separator: ", "))
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        Text("ISBN: \(book.primaryISBN)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(.vertical, 4)
            }
            .listStyle(.plain)
        }
        .padding()
        .navigationTitle("Book Discovery")
    }
}
