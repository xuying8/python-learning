import SwiftUI

struct RootTabView: View {
    @EnvironmentObject private var container: AppContainer

    var body: some View {
        TabView {
            NavigationStack {
                BookSearchView(viewModel: container.searchViewModel)
            }
            .tabItem {
                Label("Discover", systemImage: "magnifyingglass")
            }

            NavigationStack {
                BookshelfView(viewModel: container.bookshelfViewModel)
            }
            .tabItem {
                Label("Library", systemImage: "books.vertical")
            }

            NavigationStack {
                ImportView(viewModel: container.bookshelfViewModel)
            }
            .tabItem {
                Label("Import", systemImage: "square.and.arrow.down")
            }
        }
        .tint(.indigo)
    }
}
