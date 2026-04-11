import SwiftUI

struct BookshelfView: View {
    @ObservedObject var viewModel: BookshelfViewModel

    var body: some View {
        VStack(spacing: 12) {
            header

            Picker("Sort", selection: $viewModel.sortType) {
                ForEach(BookshelfViewModel.SortType.allCases, id: \.self) { item in
                    Text(item.rawValue).tag(item)
                }
            }
            .pickerStyle(.segmented)

            List(viewModel.filteredBooks) { book in
                NavigationLink(value: book) {
                    BookRowCard(book: book)
                }
            }
            .listStyle(.plain)
            .searchable(text: $viewModel.searchText, prompt: "Search imported books")
        }
        .padding(.horizontal)
        .navigationTitle("My Library")
        .navigationDestination(for: ImportedBook.self) { book in
            ReaderScreen(book: book)
        }
    }

    private var header: some View {
        HStack {
            VStack(alignment: .leading) {
                Text("Total Books")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text("\(viewModel.books.count)")
                    .font(.system(size: 30, weight: .bold))
            }
            Spacer()
            Label("Local only", systemImage: "lock.shield")
                .font(.caption)
                .padding(8)
                .background(Color.green.opacity(0.12))
                .clipShape(Capsule())
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }
}

private struct BookRowCard: View {
    let book: ImportedBook

    var body: some View {
        HStack(spacing: 12) {
            RoundedRectangle(cornerRadius: 10)
                .fill(Color.accentColor.opacity(0.15))
                .frame(width: 42, height: 56)
                .overlay(Image(systemName: "book.closed").foregroundStyle(.accent))

            VStack(alignment: .leading, spacing: 4) {
                Text(book.title).font(.headline)
                Text(book.format.rawValue.uppercased())
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Image(systemName: "chevron.right")
                .foregroundStyle(.tertiary)
        }
        .padding(.vertical, 4)
    }
}

private struct ReaderScreen: View {
    @EnvironmentObject private var container: AppContainer
    let book: ImportedBook

    var body: some View {
        ReaderView(book: book, readerViewModel: container.readerViewModel, summaryViewModel: container.summaryViewModel)
    }
}
