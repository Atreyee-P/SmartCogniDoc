//
//  Models.swift
//  SmartCogniDoc
//
//  Created by Atreyee on 28.09.2026.
//

import Foundation

struct IngestResponse: Codable {
    let document_id: String
    let filename: String
    let pages: Int
    let chunks: Int
}

struct AskRequest: Codable {
    let document_id: String
    let question: String
}

struct AskResponse: Codable {
    let answer: String
    let citations: [Int]
    let retrieved_pages: [Int]
}
