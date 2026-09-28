//
//  APIClient.swift
//  SmartCogniDoc
//
//  Created by Atreyee on 28.09.2026.
//

import Foundation

final class APIClient {
    private let baseURL = AppConfig.apiBaseURL

    func uploadPDF(url: URL) async throws -> IngestResponse {
        var request = URLRequest(url: baseURL.appendingPathComponent("ingest"))
        request.httpMethod = "POST"

        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue(
            "multipart/form-data; boundary=\(boundary)",
            forHTTPHeaderField: "Content-Type"
        )

        let pdfData = try Data(contentsOf: url)
        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append(
            "Content-Disposition: form-data; name=\"file\"; filename=\"\(url.lastPathComponent)\"\r\n"
                .data(using: .utf8)!
        )
        body.append("Content-Type: application/pdf\r\n\r\n".data(using: .utf8)!)
        body.append(pdfData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        let (data, response) = try await URLSession.shared.data(for: request)
        try validate(response)
        return try JSONDecoder().decode(IngestResponse.self, from: data)
    }

    func ask(documentID: String, question: String) async throws -> AskResponse {
        var request = URLRequest(url: baseURL.appendingPathComponent("ask"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(
            AskRequest(document_id: documentID, question: question)
        )

        let (data, response) = try await URLSession.shared.data(for: request)
        try validate(response)
        return try JSONDecoder().decode(AskResponse.self, from: data)
    }

    private func validate(_ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse,
              200..<300 ~= http.statusCode else {
            throw URLError(.badServerResponse)
        }
    }
}
