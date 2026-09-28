//
//  AppConfig.swift
//  SmartCogniDoc
//
//  Created by Atreyee on 28.09.2026.
//

import Foundation

enum AppConfig {
    // Safe public default for the iOS Simulator when FastAPI runs on the Mac.
    // For a physical iPhone, change this to your Mac's LAN address locally.
    static let apiBaseURL = URL(string: "http://127.0.0.1:8000")!
}
