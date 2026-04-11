# ReadingAssistant (SwiftUI)

Production-oriented iOS reading assistant sample app using Swift + SwiftUI + MVVM.

## Features
- Douban book search (title/author/ISBN/cover)
- Import EPUB/TXT with `UIDocumentPickerViewController`
- Read TXT and basic EPUB content in app
- Convert EPUB to TXT locally
- Summarize TXT content with OpenAI-compatible API
- CoreData-backed bookshelf metadata and summary cache

## Structure
See `ReadingAssistant/` for app source modules.

## Setup
1. Open `ReadingAssistant.xcodeproj` (create one in Xcode and add these files).
2. Add SPM dependencies:
   - [ZIPFoundation](https://github.com/weichsel/ZIPFoundation)
   - [SwiftSoup](https://github.com/scinfu/SwiftSoup)
3. In `AIService.swift`, provide API key securely (Keychain/env/config file).
4. Run on iOS 16+.

## Compliance
- No piracy website integration.
- Content source is only user-imported files or metadata APIs.
