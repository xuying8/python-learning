import SwiftUI

@main
struct ReadingAssistantApp: App {
    @StateObject private var container = AppContainer()

    var body: some Scene {
        WindowGroup {
            RootTabView()
                .environmentObject(container)
                .environment(\.managedObjectContext, container.persistence.controller.viewContext)
        }
    }
}
