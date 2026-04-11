import SwiftUI

struct BookshelfView: View {
    @ObservedObject var viewModel: BookshelfViewModel

    var body: some View {
        List(viewModel.books) { book in
            NavigationLink(value: book) {
                VStack(alignment: .leading) {
                    Text(book.title).font(.headline)
                    Text(book.format.rawValue.uppercased()).font(.caption)
                }
            }
        }
        .navigationTitle("Bookshelf")
        .navigationDestination(for: ImportedBook.self) { book in
            ReaderScreen(book: book)
        }
    }
}

private struct ReaderScreen: View {
    @EnvironmentObject private var container: AppContainer
    let book: ImportedBook

    var body: some View {
        ReaderView(book: book, readerViewModel: container.readerViewModel, summaryViewModel: container.summaryViewModel)
    }
}
