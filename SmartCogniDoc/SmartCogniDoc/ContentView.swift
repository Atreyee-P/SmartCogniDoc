//
//  ContentView.swift
//  SmartCogniDoc
//
//  Created by Atreyee on 28.09.2026.
//

import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    @State private var showImporter = false
    @State private var working = false
    @State private var documentID: String?
    @State private var status = "Upload a PDF to start."
    @State private var question = ""
    @State private var answer = ""
    @State private var citations: [Int] = []

    private let api = APIClient()

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                Text("SmartCogniDoc")
                    .font(.largeTitle.bold())

                Text("Local Vision • RAG • LLM")
                    .foregroundStyle(.secondary)

                Button("Upload PDF") {
                    showImporter = true
                }
                .buttonStyle(.borderedProminent)
                .disabled(working)

                Text(status)
                    .font(.footnote)
                    .foregroundStyle(.secondary)

                if documentID != nil {
                    TextField("Ask a question about the document", text: $question)
                        .textFieldStyle(.roundedBorder)

                    Button("Ask SmartCogniDoc") {
                        Task { await askQuestion() }
                    }
                    .buttonStyle(.bordered)
                    .disabled(
                        question.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                        || working
                    )

                    if !answer.isEmpty {
                        ScrollView {
                            VStack(alignment: .leading, spacing: 12) {
                                Text("Answer")
                                    .font(.headline)
                                Text(answer)

                                if !citations.isEmpty {
                                    Text(
                                        "Sources: pages \(citations.map(String.init).joined(separator: ", "))"
                                    )
                                    .font(.footnote)
                                    .foregroundStyle(.secondary)
                                }
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                }

                if working {
                    ProgressView("Processing locally…")
                }

                Spacer()
            }
            .padding()
            .navigationTitle("Document AI")
            .fileImporter(
                isPresented: $showImporter,
                allowedContentTypes: [.pdf],
                allowsMultipleSelection: false
            ) { result in
                switch result {
                case .success(let urls):
                    if let url = urls.first {
                        Task { await upload(url) }
                    }
                case .failure(let error):
                    status = "Error: \(error.localizedDescription)"
                }
            }
        }
    }

    private func upload(_ url: URL) async {
        working = true
        status = "Reading document locally…"
        answer = ""
        citations = []

        do {
            let result = try await api.uploadPDF(url: url)
            documentID = result.document_id
            status = "\(result.filename) • \(result.pages) pages • \(result.chunks) RAG chunks"
        } catch {
            status = "Upload error: \(error.localizedDescription)"
        }

        working = false
    }

    private func askQuestion() async {
        guard let documentID else { return }

        working = true
        status = "Retrieving relevant chunks and generating answer…"

        do {
            let result = try await api.ask(documentID: documentID, question: question)
            answer = result.answer
            citations = result.citations
            status = "Answer generated locally."
        } catch {
            status = "Question error: \(error.localizedDescription)"
        }

        working = false
    }
}

